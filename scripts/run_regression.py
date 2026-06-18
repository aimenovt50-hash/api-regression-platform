#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run API regression suite")
    parser.add_argument("--env", default="local")
    parser.add_argument("--markers", default="regression or smoke or contract")
    parser.add_argument("--parallel", action="store_true")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "pytest", f"--env={args.env}", "-m", args.markers]
    if args.parallel:
        cmd.extend(["-n", "auto"])
    return subprocess.run(cmd, cwd=project_root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
