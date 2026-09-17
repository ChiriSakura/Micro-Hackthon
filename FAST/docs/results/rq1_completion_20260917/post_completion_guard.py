import json, sys
from pathlib import Path
out, run = map(Path, sys.argv[1:])
try:
    verification = json.loads((out/'archive_verification.json').read_text())
    result = json.loads((out/'results.json').read_text())
    complete = verification.get('passed') is True and (out/'artifacts.tar.gz').stat().st_size > 0 and Path(result['run']) == run and 'token_totals' in result
except (OSError, ValueError, KeyError):
    complete = False
raise SystemExit(0 if complete else 1)
