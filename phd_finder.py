"""Convenience wrapper for running the PhDFinder academic profile."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from jobfinder.pipeline.cli import phd_main

if __name__ == "__main__":
    sys.exit(phd_main())
