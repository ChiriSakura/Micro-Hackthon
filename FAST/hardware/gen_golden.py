"""为 DynaX RTL 模块生成 golden 向量。

命令行入口；参照模型本身在 `golden/` 包里，按被测单元分文件。

    python gen_golden.py --module RePE --out golden.json

`--module` 的取值和 `chisel/Elaborate.scala` 的 elaborate 目标一一对应，
`slurm/rtl/fast_rtl_verify_all.slurm` 里的表把两者绑在一起。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from golden.exp_unit import exp_cases
from golden.execute_unit import (
    repe_array_cases,
    repe_cases,
    repe_row_cases,
    sram_cases,
)
from golden.fixedpoint import quantise
from golden.predict_unit import (
    prepe_array_14_cases,
    prepe_array_cases,
    prepe_cases,
    psum_softmax_cases,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", default="TopK",
                        choices=["TopK", "ExpUnit", "PSumSoftmax", "SRAM",
                                 "RePE", "RePERow", "RePEArray", "PrePE",
                                 "PrePEArray", "PrePEArray14"])
    parser.add_argument("--height", type=int, default=2)
    parser.add_argument("--width", type=int, default=8)
    parser.add_argument("--out-bits", type=int, default=12)
    parser.add_argument("--reg-width", type=int, default=8)
    parser.add_argument("--pe-count", type=int, default=8)
    parser.add_argument("--num-rows", type=int, default=4)
    parser.add_argument("--bank-count", type=int, default=4)
    parser.add_argument("--bank-depth", type=int, default=256)
    parser.add_argument("--bank-width", type=int, default=64)
    parser.add_argument("--frac", type=int, default=4, help="ExpUnit LUT index bits")
    parser.add_argument("--guard", type=int, default=4, help="ExpUnit rounding guard bits")
    parser.add_argument("--m", type=int, default=64, help="block width")
    parser.add_argument("--n", type=int, default=16, help="values kept per block")
    parser.add_argument("--bits", type=int, default=16)
    parser.add_argument("--point", type=int, default=8)
    parser.add_argument("--cases", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260905)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.module == "PrePEArray14":
        cases = prepe_array_14_cases(args.height, args.width, args.out_bits,
                                     args.bits, args.point, args.seed)
        payload = {
            "module": "PrePEArray_1_4",
            "params": {"height": args.height, "width": args.width,
                       "outBits": args.out_bits, "bits": args.bits,
                       "point": args.point},
            "reference": (
                "DynaX's own quant_qk_matmul('1_4_6bit'), through a structural "
                "model of the array"
            ),
            "seed": args.seed, "cases": cases,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        total = sum(sum(c["expected_idx"]) for c in cases)
        print(f"wrote {len(cases)} PrePEArray_1_4 cases ({total} checked cycles) to {args.out}")
        return 0

    if args.module == "PrePEArray":
        cases = prepe_array_cases(args.height, args.width, args.out_bits,
                                  args.bits, args.point, args.seed)
        payload = {
            "module": "PrePEArray",
            "params": {"height": args.height, "width": args.width,
                       "outBits": args.out_bits, "bits": args.bits,
                       "point": args.point},
            "reference": (
                "DynaX's own quant_qk_matmul('1_2_4bit'), through a structural "
                "model of the array"
            ),
            "seed": args.seed, "cases": cases,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        total = sum(sum(c["expected_idx"]) for c in cases)
        print(f"wrote {len(cases)} PrePEArray cases ({total} checked cycles) to {args.out}")
        return 0

    if args.module == "PrePE":
        payload = {
            "module": "PrePE",
            "params": {"outBits": args.out_bits},
            "reference": "cycle-accurate mirror of the PrePE_1_2 state machine",
            "seed": args.seed,
            "cases": prepe_cases(args.out_bits, args.seed),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        total = sum(len(c["input_ticks"]) // 6 for c in payload["cases"])
        print(f"wrote {len(payload['cases'])} PrePE cases ({total} cycles) to {args.out}")
        return 0

    if args.module in ("RePERow", "RePEArray"):
        if args.module == "RePERow":
            cases = repe_row_cases(args.pe_count, args.bits, args.point,
                                   args.reg_width, args.seed)
            params = {"peCount": args.pe_count, "regWidth": args.reg_width}
        else:
            cases = repe_array_cases(args.num_rows, args.pe_count, args.bits,
                                     args.point, args.reg_width, args.seed)
            params = {"numRows": args.num_rows, "peCountPerRow": args.pe_count,
                      "regWidth": args.reg_width}
        params |= {"bits": args.bits, "point": args.point}
        payload = {
            "module": args.module, "params": params,
            "reference": "cycle-accurate structural model composed from RePEModel",
            "seed": args.seed, "cases": cases,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        total = sum(sum(c["expected_idx"]) for c in cases)
        print(f"wrote {len(cases)} {args.module} cases ({total} checked cycles) to {args.out}")
        return 0

    if args.module == "RePE":
        payload = {
            "module": "RePE",
            "params": {
                "bits": args.bits, "point": args.point, "regWidth": args.reg_width,
            },
            "reference": "cycle-accurate mirror of the RePE control FSM and datapath",
            "seed": args.seed,
            "cases": repe_cases(args.bits, args.point, args.reg_width, args.seed),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        total = sum(len(c["expected_value_ticks"]) for c in payload["cases"])
        print(f"wrote {len(payload['cases'])} RePE cases ({total} cycles) to {args.out}")
        return 0

    if args.module == "PSumSoftmax":
        payload = {
            "module": "PSumSoftmax",
            "params": {"bits": args.bits, "point": args.point},
            "reference": "bit-exact mirror of the Chisel datapath, truncations included",
            "seed": args.seed,
            "cases": psum_softmax_cases(args.bits, args.point, args.seed),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        total = sum(len(c["input_ticks"]) // 4 for c in payload["cases"])
        print(f"wrote {len(payload['cases'])} PSumSoftmax cases ({total} points) to {args.out}")
        return 0

    if args.module == "SRAM":
        payload = {
            "module": "SRAM",
            "params": {
                "bankCount": args.bank_count, "bankDepth": args.bank_depth,
                "bankWidth": args.bank_width,
            },
            "reference": "a correct banked synchronous-read SRAM, read latency 1",
            "seed": args.seed,
            "cases": sram_cases(args.bank_count, args.bank_depth,
                                args.bank_width, args.seed),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        total = sum(sum(c["expected_idx"]) for c in payload["cases"])
        print(f"wrote {len(payload['cases'])} SRAM cases ({total} checked reads) to {args.out}")
        return 0

    if args.module == "ExpUnit":
        payload = {
            "module": "ExpUnit",
            "params": {
                "bits": args.bits, "point": args.point,
                "frac": args.frac, "guard": args.guard,
            },
            "reference": "bit-exact mirror of the Chisel shift-and-LUT datapath",
            "seed": args.seed,
            "cases": exp_cases(args.bits, args.point, args.frac, args.guard, args.seed),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        total = sum(len(c["input_ticks"]) for c in payload["cases"])
        print(f"wrote {len(payload['cases'])} ExpUnit cases ({total} points) to {args.out}")
        return 0

    generator = torch.Generator().manual_seed(args.seed)
    cases = []
    for index in range(args.cases):
        if index == 0:
            raw = torch.linspace(-1.0, 1.0, args.m)            # monotone ramp
        elif index == 1:
            raw = torch.zeros(args.m)                          # all ties at zero
        elif index == 2:
            raw = torch.full((args.m,), 0.5)                   # all equal, non-zero
        elif index == 3:
            # Decisive case A: the block's LAST element holds the largest value.
            raw = torch.randn(args.m, generator=generator) * 0.3
            raw[args.m - 1] = 0.9
        elif index == 4:
            # Decisive case B: the last element holds the SECOND largest value.
            # If the block-boundary clear drops it, this is where it shows.
            raw = torch.randn(args.m, generator=generator) * 0.3
            raw[args.m - 1] = 0.8
            raw[0] = 0.9
        elif index == 5:
            # Decisive case C: the last element is mid-ranked but still top-n.
            raw = torch.linspace(0.9, -0.9, args.m)
            raw[args.m - 1] = 0.5
        else:
            raw = torch.randn(args.m, generator=generator) * 0.4

        values = quantise(raw, args.bits, args.point)
        best = torch.topk(values, args.n, largest=True, sorted=True)
        scale = 1 << args.point
        cases.append({
            "name": ["ramp", "zeros", "ties", "last_is_1st", "last_is_2nd", "last_is_mid",
                     *[f"random_{i}" for i in range(args.cases)]][index],
            "input_ticks": [int(round(float(v) * scale)) for v in values],
            "expected_value_ticks": [int(round(float(v) * scale)) for v in best.values],
            "expected_idx": [int(i) for i in best.indices],
        })

    payload = {
        "module": "TopK",
        "params": {"m": args.m, "n": args.n, "bits": args.bits, "point": args.point},
        "reference": "torch.topk on the module's fixed-point grid",
        "seed": args.seed,
        "cases": cases,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(cases)} golden cases to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
