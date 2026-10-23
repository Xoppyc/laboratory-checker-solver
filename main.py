#!/usr/bin/env python3
"""Entry point for the Laboratory Checker Quiz Solver."""

import os
import sys
from pathlib import Path


def load_dotenv_fallback(dotenv_path: Path) -> None:
    """Lightweight fallback parser for .env files without requiring external packages."""
    if not dotenv_path.is_file():
        return
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'\"")
        if key not in os.environ:
            os.environ[key] = val


# Attempt to load .env file
env_file = Path(__file__).resolve().parent / ".env"
try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=env_file)
except ImportError:
    load_dotenv_fallback(env_file)

# Ensure src is on sys.path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from checker_solver.cli import main

if __name__ == "__main__":
    main()

