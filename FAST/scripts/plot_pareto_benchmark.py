"""Export a labelled scientific figure from the equal-budget pilot JSON."""
import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    payload = json.loads(args.results.read_text())
    labels = sorted({r["label"] for r in payload["runs"]})
    methods = sorted({r["method"] for r in payload["runs"]})
    fig, axes = plt.subplots(1, len(labels), figsize=(6*len(labels), 4.5), squeeze=False)
    for ax, label in zip(axes[0], labels):
        for i, method in enumerate(methods):
            points = {tuple(x) for r in payload["runs"]
                      if r["label"] == label and r["method"] == method and r["trace"]
                      for x in r["trace"][-1]["frontier"]}
            ax.scatter([x*1e6 for x, _ in points], [y*1e6 for _, y in points],
                       label=method, marker=["o", "s", "x", "^", "+"][i % 5],
                       s=100, alpha=.7)
        ax.set(xlabel="Predicted latency per task (µs)",
               ylabel="Partial-model energy per task (µJ)", title=label)
        ax.grid(alpha=.2)
        ax.legend()
    fig.suptitle("Equal-budget search pilot · L1 shared model · NOT measured accelerator energy")
    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=180)
    fig.savefig(args.out.with_suffix(".pdf"))
    plt.close(fig)


if __name__ == "__main__":
    main()
