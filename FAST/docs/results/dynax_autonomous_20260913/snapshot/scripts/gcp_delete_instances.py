"""Delete the instances a CHIA cluster created. A last-resort teardown.

`chia down` is the normal path. This exists because a teardown that fails leaves
machines billing, so the safety net must not itself depend on CHIA being able to
run, or on an interactive terminal being present.

Only instances labelled with the given cluster are touched.
"""

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default=os.environ.get("GCP_PROJECT"))
    parser.add_argument("--zone", default=os.environ.get("GCP_ZONE", "us-central1-a"))
    parser.add_argument("--cluster", required=True, help="value of the chia-cluster label")
    parser.add_argument("--yes", action="store_true", help="required; without it nothing is deleted")
    args = parser.parse_args()
    if not args.project:
        print("no project: pass --project or set GCP_PROJECT", file=sys.stderr)
        return 1

    import google.auth
    from google.cloud import compute_v1

    credentials, _ = google.auth.default()
    client = compute_v1.InstancesClient(credentials=credentials)
    targets = [
        instance for instance in client.list(project=args.project, zone=args.zone, timeout=60)
        if instance.labels.get("chia-cluster") == args.cluster
    ]
    if not targets:
        print(f"no instances labelled chia-cluster={args.cluster} in {args.project}/{args.zone}")
        return 0

    for instance in targets:
        print(f"{'deleting' if args.yes else 'would delete'} {instance.name} ({instance.status})")
    if not args.yes:
        print("nothing deleted; pass --yes to actually delete")
        return 0

    failures = 0
    for instance in targets:
        try:
            client.delete(project=args.project, zone=args.zone, instance=instance.name, timeout=120).result(timeout=300)
            print(f"deleted {instance.name}")
        except Exception as exc:
            failures += 1
            print(f"FAILED to delete {instance.name}: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
