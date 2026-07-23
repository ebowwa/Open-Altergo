"""Hugging Face Spaces-compatible launcher for the Gradio application."""

from apps.gradio.app import build_app, demo, main, run

__all__ = ["build_app", "demo", "main", "run"]

if __name__ == "__main__":
    main()
