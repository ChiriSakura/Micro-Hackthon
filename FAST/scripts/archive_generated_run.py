#!/usr/bin/env python3
"""Create or verify a portable FAST archive, without LLM calls or input deletion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.fullstack.artifacts import create_archive, verify_archive
from fast.fullstack.library import save


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--input", action="append", metavar="LABEL=PATH",
                        help="Repeat for run, source, validation, or development evidence")
    action.add_argument("--verify", type=Path)
    parser.add_argument("--output", type=Path, help="New .tar.gz path for creation")
    parser.add_argument("--record", type=Path, required=True, help="Verification JSON output")
    args = parser.parse_args(argv)
    if args.verify:
        result = verify_archive(args.verify)
    else:
        if args.output is None:
            parser.error("--output is required when creating an archive")
        inputs = {}
        for item in args.input:
            label, separator, path = item.partition("=")
            if not separator or not path or label in inputs:
                parser.error("Each input must be a unique LABEL=PATH")
            inputs[label] = Path(path)
        result = create_archive(inputs, args.output)
    save(args.record, result)
    print(json.dumps({k: v for k, v in result.items() if k != "manifest"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
