"""List Compute Engine instances in a zone. Read-only, and fast.

The teardown path needs to confirm that nothing is left billing, so it must not
depend on the gcloud CLI, which takes over a minute to start from shared storage.

Exit code is 0 when the zone is empty and 2 when instances remain, so a shell
script can branch on it.
"""

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default=os.environ.get("GCP_PROJECT"))
    parser.add_argument("--zone", default=os.environ.get("GCP_ZONE", "us-central1-a"))
    parser.add_argument("--quiet", action="store_true", help="print nothing; use the exit code")
    args = parser.parse_args()
    if not args.project:
        print("no project: pass --project or set GCP_PROJECT", file=sys.stderr)
        return 1

    import google.auth
    from google.cloud import compute_v1

    credentials, _ = google.auth.default()
    client = compute_v1.InstancesClient(credentials=credentials)
    instances = list(client.list(project=args.project, zone=args.zone, timeout=60))

    if not args.quiet:
        for instance in instances:
            print(f"{instance.name}\t{instance.status}\t{instance.machine_type.split('/')[-1]}")
        if not instances:
            print(f"(no instances in {args.project}/{args.zone})")
    return 2 if instances else 0


if __name__ == "__main__":
    raise SystemExit(main())
