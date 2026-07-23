"""Tests for the application package."""
"""Test package setup for the local src-layout package."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (
    PROJECT_ROOT / "apis" / "python_api" / "src",
    PROJECT_ROOT / "cloud" / "engine" / "src",
)
for source_root in SOURCE_ROOTS:
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
