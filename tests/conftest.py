"""Pytest setup for local imports."""

import sys
from pathlib import Path


def pytest_configure(config):
    repo_root = Path(__file__).resolve().parents[1]
    src_path = str(repo_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
