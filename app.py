"""Compatibility launcher for the packaged Gradio interface."""

from silent_speech.interfaces.gradio_app import build_app, demo, main, run

__all__ = ["build_app", "demo", "main", "run"]

if __name__ == "__main__":
    main()
