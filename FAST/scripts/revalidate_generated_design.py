#!/usr/bin/env python3
"""Recheck one archived generated design without making any LLM calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.fullstack.tools import RtlTools
from fast.fullstack.revalidation import revalidate


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--round',type=int,required=True)
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--tool-root',type=Path,required=True)
    parser.add_argument('--ppa-backend',choices=['yosys_opensta','hammer_openroad'])
    parser.add_argument('--timeout',type=int,default=300)
    args=parser.parse_args(argv)
    result=revalidate(args.run,args.round,args.catalog,args.output,RtlTools(args.tool_root,args.timeout),ppa_backend=args.ppa_backend)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
