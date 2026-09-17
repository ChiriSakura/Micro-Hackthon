"""Run the new generation flow: python -m fast.fullstack.cli --help."""
import argparse
import json
from pathlib import Path

from fast.agents.llm_backends import VertexDirect
from .contracts import Task
from .flow import FullStackFlow
from .tools import RtlTools


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--run-dir', type=Path, required=True, help='New directory; existing results are never overwritten')
    parser.add_argument('--tool-root', type=Path, required=True, help='Contains containers/ and pdk/nangate45/')
    parser.add_argument('--project', required=True)
    parser.add_argument('--location', default='us-central1')
    parser.add_argument('--model', default='gemini-2.5-pro')
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--tool-timeout', type=int, help='Per-tool timeout; independent of LLM timeout (Hammer may need 3600 s)')
    parser.add_argument('--max-output-tokens', type=int, default=24000)
    parser.add_argument('--critic', choices=['on', 'off'], default='on')
    parser.add_argument('--initial-run', type=Path, help='Shared verified starting design; rebuild and remeasure, never reuse PPA')
    args = parser.parse_args(argv)
    task = Task.parse(json.loads(args.task.read_text()))
    llm = VertexDirect(model=args.model, project=args.project, location=args.location,
                       timeout_seconds=args.timeout, max_output_tokens=args.max_output_tokens)
    flow = FullStackFlow(task, args.catalog, args.run_dir, llm,
                        RtlTools(args.tool_root, args.tool_timeout or args.timeout), critic_enabled=args.critic == 'on', initial_run=args.initial_run)
    result = flow.run()
    print(json.dumps({k:v for k,v in result.items() if k != 'rounds'}, indent=2, ensure_ascii=False))
    return 0 if result['pareto_rounds'] and result['status'] not in ('failed', 'reference_integrity_failed', 'ppa_failed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
