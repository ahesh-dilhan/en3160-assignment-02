"""Run from the repository with: python scripts/run_assignment.py --task q1."""
import argparse
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / "tmp/matplotlib"))

import matplotlib
matplotlib.use("Agg")

from assignment2.common import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["q1", "q2", "q3", "q4", "all"], default="all")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    tasks = ["q1", "q2", "q3", "q4"] if args.task == "all" else [args.task]
    import importlib
    for task in tasks:
        module = importlib.import_module("assignment2." + {
            "q1": "blobs", "q2": "ransac", "q3": "compositing", "q4": "registration"}[task])
        print(f"Running {task}...", flush=True)
        module.run(args.output / task)
        print(f"Saved {task}: {args.output / task}", flush=True)


if __name__ == "__main__":
    main()
