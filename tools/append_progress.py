"""Append a timestamped entry to PROGRESS_LOG.md.

Usage:
    .venv\\Scripts\\python.exe tools\\append_progress.py \
        --task "what was done" --result "outcome / verification"
"""
import argparse
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "PROGRESS_LOG.md"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="what was done")
    parser.add_argument("--result", required=True, help="outcome / verification")
    args = parser.parse_args()

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"- [{ts}] Task: {args.task} -> {args.result}\n")
    print(f"Progress log updated: {LOG}")


if __name__ == "__main__":
    main()
