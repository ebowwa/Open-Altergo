"""Hugging Face Spaces-compatible launcher for the Gradio application."""

import sys
from pathlib import Path


PACKAGE_SRC = Path(__file__).resolve().parent / "packages" / "silent_speech" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from apps.gradio.app import build_app, demo, main, run  # noqa: E402

__all__ = ["build_app", "demo", "main", "run"]

if __name__ == "__main__":
    main()
