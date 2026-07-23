"""Gradio adapter for the interface-neutral silent-speech service."""

import traceback
from collections.abc import Callable

import gradio as gr

from silent_speech.core import RuntimeConfig, SilentSpeechService


TIPS = """
### Tips for best accuracy
- **Bright light on your face** (face a window or lamp — not backlit)
- **Look at the camera**, face filling the frame, roughly eye-level
- **Articulate a little more deliberately** than normal
- Leave a **~1 second pause between sentences**; keep each sentence ≥ ~1s
- It reads **lips only** — sound is never used
"""


def format_transcription(output):
    """Convert a core transcription result into Gradio textbox values."""

    if not output.get("segments"):
        return (
            "No face / no speech detected. Try better lighting and face the "
            "camera.",
            "",
        )

    lines = []
    for segment in output["segments"]:
        if not segment["text"]:
            continue
        start, end = segment["seg_time"]
        lines.append(f"[{start:4.1f}–{end:4.1f}s]  {segment['text']}")

    transcript = output.get("transcript", "").strip() or "(nothing recognized)"
    return transcript, "\n".join(lines)


def create_handler(
    service: SilentSpeechService,
) -> Callable[[str | None, bool], tuple[str, str]]:
    """Create a UI callback around any compatible core service."""

    def handle(video, flip):
        if not video:
            return "Please record or upload a video first.", ""
        try:
            output = service.transcribe(video, nbest=5, hflip=bool(flip))
        except Exception:
            return f"Error:\n{traceback.format_exc()}", ""
        return format_transcription(output)

    return handle


default_service = SilentSpeechService(RuntimeConfig.from_env())
run = create_handler(default_service)


def build_app(service: SilentSpeechService | None = None) -> gr.Blocks:
    """Build the Gradio UI without forcing the model to load."""

    handler = run if service is None else create_handler(service)
    with gr.Blocks(title="Silent Lip Reader") as interface:
        gr.Markdown(
            "# 👄 Silent Lip Reader\n"
            "Record yourself (or upload) — it reads your **lips only**, "
            "no sound used, and writes what you said."
        )
        with gr.Row():
            with gr.Column():
                video = gr.Video(
                    sources=["webcam", "upload"],
                    label="Record (webcam) or upload a clip",
                )
                flip = gr.Checkbox(
                    value=False,
                    label=(
                        "Flip horizontally — only tick if the transcript comes "
                        "out as gibberish (some setups mirror the video)"
                    ),
                )
                button = gr.Button("Read my lips", variant="primary")
                gr.Markdown(TIPS)
            with gr.Column():
                transcript = gr.Textbox(label="Transcript (lip-read)", lines=4)
                breakdown = gr.Textbox(
                    label="Per-utterance breakdown",
                    lines=10,
                )

        button.click(
            handler,
            inputs=[video, flip],
            outputs=[transcript, breakdown],
        )
    return interface


demo = build_app()


def main():
    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
