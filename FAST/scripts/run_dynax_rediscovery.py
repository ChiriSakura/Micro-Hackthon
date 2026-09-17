"""Fresh DynaX N1/N2/M/T0/T1 + schedule/hardware search, optionally replayed in RTL."""
import argparse
from dataclasses import fields
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fast.adapters.dynax import DynaXKernelAdapter, _dataset_flag
from fast.agents.codesign import CoDesignSpace
from fast.agents.cooptimizer import RandomProposer
from fast.agents.rediscovery import DynaXRediscovery, RandomKernelProposer
from fast.agents.rediscovery_critic import build_search_critic, read_validation_evidence, review_search, search_context
from fast.agents.proposers import LLMProposer
from fast.agents.plan_proposers import LLMPlanProposer
from fast.schemas.models import ArchSpecs, Budget, ExperimentSpec, KernelSearchSpace
from fast.schemas.models import kernel_measurement_from_dict
from fast.schemas.conversions import kernel_result_from_measurement


def load_config(path):
    config = json.loads(path.read_text())
    domains = config["hardware_space"]
    required = {f.name for f in fields(CoDesignSpace)}
    if set(domains) != required or any(not v for v in domains.values()):
        raise ValueError(f"supply every hardware domain explicitly: {sorted(required)}")
    kernel = config["kernel_space"]
    if set(kernel) != {"block_ms", "xm_high", "xm_low", "threshold_pairs"}:
        raise ValueError("supply M, N1, N2 and threshold_pairs explicitly")
    space = KernelSearchSpace(algorithm="xm", max_sequence_length=config["task"]["sequence_length"],
        **{k: tuple(tuple(p) if isinstance(p, list) else p for p in v) for k, v in kernel.items()})
    if not space.labels():
        raise ValueError("kernel search space is empty")
    return config, space, CoDesignSpace(**{k: tuple(v) for k, v in domains.items()})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--method", choices=["llm", "random"], required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--dynax-python", required=True)
    p.add_argument("--device", default="cpu")
    p.add_argument("--gcp-project", default=os.environ.get("GCP_PROJECT"))
    p.add_argument("--gcp-location", default="us-central1")
    p.add_argument("--llm-model", default="gemini-2.5-pro")
    p.add_argument("--critic", choices=["auto", "rule", "llm", "off"], default="auto",
                   help="auto: LLM Critic for llm search, rule Critic for random; off is the ablation")
    p.add_argument("--validate-frontier", action="store_true")
    p.add_argument("--containers", type=Path)
    p.add_argument("--liberty", type=Path)
    args = p.parse_args()
    critic_mode = args.method if args.critic == "auto" else args.critic
    critic_mode = "rule" if critic_mode == "random" else critic_mode
    config, kernel_space, hardware_space = load_config(args.config)
    if args.validate_frontier and (not args.containers or not args.liberty):
        p.error("RTL validation requires --containers and --liberty")
    if (args.method == "llm" or critic_mode == "llm") and not args.gcp_project:
        p.error("LLM search/Critic requires --gcp-project")
    args.out.mkdir(parents=True, exist_ok=False)
    task, budgets = config["task"], config["budgets"]
    spec = ExperimentSpec(
        experiment_id="dynax-rediscovery", candidate_id=f"{args.method}-{args.seed}",
        model=task["model"], dataset=task["dataset"], sequence_length=task["sequence_length"],
        # Compatibility metadata only: actual measurements always use proposed
        # six-field labels, never this ExperimentSpec's single-point defaults.
        sparsity_x=min(kernel_space.xm_low), sparsity_m=max(kernel_space.block_ms),
        epsilon=task["epsilon"], seed=task["data_seed"], max_samples=task["max_samples"],
        dtype=task["dtype"], budget=Budget(max_candidates=budgets["kernel"],
            max_evaluations=budgets["kernel"], max_wall_seconds=budgets["wall_seconds"]))
    random_kernel = RandomKernelProposer(args.seed)
    llm = None
    if args.method == "llm" or critic_mode == "llm":
        from fast.agents.llm_backends import VertexDirect
        llm = VertexDirect(model=args.llm_model, project=args.gcp_project,
                           location=args.gcp_location, temperature=.2, timeout_seconds=180,
                           system_message="Explore the supplied design space using tool feedback.")
    if args.method == "llm":
        proposer = LLMProposer(llm, model_name=args.llm_model, fallback=random_kernel)
        factory = lambda index: LLMPlanProposer(llm, model_name=args.llm_model,
            fallback=RandomProposer(args.seed+index), calibration_hints=False)
    else:
        proposer = random_kernel
        factory = lambda index: RandomProposer(args.seed+index)
    critic = build_search_critic(critic_mode, llm=llm, model_name=args.llm_model,
                                specs=ArchSpecs(**config["constraints"]))
    repo = ROOT.parent
    sources = [*sorted((ROOT/"fast").rglob("*.py")), Path(__file__).resolve(),
               repo/"DynaX/run_eval_matrix.py", *sorted((repo/"DynaX/models").rglob("*.py")),
               repo/"DynaX/capture_row_workload.py", repo/"DynaX/plot_attention_masks.py",
               ROOT/"scripts/validate_pareto_scheduler.py",
               ROOT/"scripts/refine_rediscovery.py",
               *sorted((ROOT/"hardware/chisel").rglob("*.scala")),
               ROOT/"hardware/tb/tb_block_scheduler.cpp", ROOT/"hardware/tb/gen_ports.py",
               ROOT/"hardware/golden/gen_workload_stimulus.py"]
    metadata = {
        "config": config, "method": args.method, "search_seed": args.seed,
        "llm_sampling_seeded": False, "calibration_hints_shown_to_llm": False,
        "llm_model": args.llm_model if llm else None,
        "source_sha256": {str(f.relative_to(repo)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "api_monetary_cost": None,
        "critic_mode": critic_mode,
    }
    def save(report):
        (args.out/"search.json").write_text(json.dumps({**report, **metadata}, indent=2, allow_nan=False))
        print(f"measured={len(report['measurements'])}, designs={len(report['designs'])}, "
              f"front={len(report['frontier'])}", flush=True)
    report = DynaXRediscovery(
        DynaXKernelAdapter(repo/"DynaX", args.out/"measurements", args.dynax_python, device=args.device),
        proposer, factory, critic=critic).run(spec, kernel_space=kernel_space, hardware_space=hardware_space,
            specs=ArchSpecs(**config["constraints"]), head_dim=task["head_dim"],
            kernel_batch=budgets["kernel_batch"], hardware_budget=budgets["hardware_per_kernel"],
            hardware_batch=budgets["hardware_batch"], checkpoint=save)
    validation = []
    for design in report["frontier"]:
        directory = args.out/"candidates"/design["design_id"]
        directory.mkdir(parents=True)
        manifest = {**design, "task": task, "evidence": report["performance_evidence"]}
        design_path = directory/"design.json"
        design_path.write_text(json.dumps(manifest, indent=2))
        point, algorithm = design["point"], design["algorithm"]
        capture = [args.dynax_python, str(repo/"DynaX/capture_row_workload.py"),
            "--model", task["model"], "--dataset", _dataset_flag(task["dataset"]), "--layer", str(task["capture_layer"]),
            "--head", str(task["capture_head"]),
            "--seq-len", str(task["sequence_length"]), "--seed", str(task["data_seed"]),
            "--methods", design["label"], "--rows", str(point["num_rows"]),
            "--block", str(algorithm["block_m"]), "--device", args.device,
            "--max-tiles", str(task["sequence_length"]**2), "--out", str(directory/"workload.json")]
        validate = [sys.executable, str(ROOT/"scripts/validate_pareto_scheduler.py"),
            "--design", str(design_path), "--workload", str(directory/"workload.json"),
            "--tile-offset", "0", "--tile-count", "0", "--out", str(directory/"rtl"),
            "--frequency-mhz", str(config["constraints"]["target_mhz"])]
        if args.containers and args.liberty:
            validate += ["--containers", str(args.containers), "--liberty", str(args.liberty)]
        (directory/"replay_commands.json").write_text(json.dumps({"capture": capture, "validate": validate}, indent=2))
        if args.validate_frontier:
            stage_results = []
            for name, command in [("capture", capture), ("validate", validate)]:
                with (directory/f"{name}.log").open("w") as log:
                    run = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                stage_results.append({"stage": name, "exit_code": run.returncode})
                if run.returncode:
                    break
            accepted, observations = read_validation_evidence(
                directory/"rtl/validation.json", design["design_id"], config["constraints"]["target_mhz"])
            validation.append({"design_id": design["design_id"], "stages": stage_results,
                               "module_verified": accepted and len(stage_results) == 2
                                   and all(s["exit_code"] == 0 for s in stage_results),
                               "observations": observations})
            measured = kernel_measurement_from_dict(next(
                m for m in report['measurements'] if m['label'] == design['label']))
            context = search_context(spec, kernel_result_from_measurement(None, measured),
                ArchSpecs(**config['constraints']), hardware_space, phase='validation',
                validation=observations, parent_point=design['point'])
            analysis = review_search(critic, context, report['critic_reviews'])
            if analysis:
                analysis['outcome']['independent_module_verified'] = validation[-1]['module_verified']
                validation[-1]['critic_review_id'] = analysis['review_id']
            save(report)
    (args.out/"validation_index.json").write_text(json.dumps(validation, indent=2))
    module_passed = any(v['module_verified'] for v in validation)
    repair_budget = budgets.get('repair_hardware', 0)
    if args.validate_frontier and validation and not module_passed and repair_budget:
        command = [sys.executable, str(ROOT/'scripts/refine_rediscovery.py'),
            '--source', str(args.out), '--out', str(args.out/'refinement'),
            '--method', args.method, '--budget', str(repair_budget),
            '--critic', critic_mode,
            '--dynax-python', args.dynax_python, '--llm-model', args.llm_model,
            '--gcp-location', args.gcp_location,
            '--containers', str(args.containers), '--liberty', str(args.liberty)]
        if args.gcp_project:
            command += ['--gcp-project', args.gcp_project]
        with (args.out/'refinement.log').open('w') as log:
            repaired = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        metadata['independent_reentry'] = {'command': command, 'exit_code': repaired.returncode,
                                          'additional_hardware_budget': repair_budget}
        module_passed = repaired.returncode == 0
    metadata["sources_unchanged"] = all(hashlib.sha256(f.read_bytes()).hexdigest() ==
        metadata["source_sha256"][str(f.relative_to(repo))] for f in sources)
    save(report)
    return 0 if metadata["sources_unchanged"] and report["frontier"] and (
        not args.validate_frontier or module_passed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
