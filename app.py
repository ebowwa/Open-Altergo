"""
Silent Lip Reader — Hugging Face Space demo.

Record yourself from the webcam (or upload a clip), and the app reads your lips
— no audio used at all — and returns a transcript. Powered by a local Auto-AVSR
visual-speech model + retinaface/FAN mouth alignment + lip-motion utterance
chunking (so it works on fully silent recordings).
"""
import os
import sys
import traceback

import gradio as gr

HERE = os.path.dirname(os.path.abspath(__file__))
# vendored ibug retinaface/FAN detectors (namespace pkg) — no pip install needed
for v in ("face_detection", "face_alignment"):
    p = os.path.join(HERE, "vendor", v)
    if os.path.isdir(p):
        sys.path.insert(0, p)
sys.path.insert(0, os.path.join(HERE, "engine"))
from pipeline import LipReader  # noqa: E402

DEVICE = os.environ.get("LIPREAD_DEVICE", "cpu")
# mediapipe ~= retinaface on diverse eval (0.547 vs 0.558) but much lighter/robust
DETECTOR = os.environ.get("LIPREAD_DETECTOR", "mediapipe")
CKPT_PATH = os.environ.get("LIPREAD_CKPT")

print(f"Loading LipReader (device={DEVICE}, detector={DETECTOR}) ...")
READER = LipReader(device=DEVICE, detector=DETECTOR, enhance=True,
                   ckpt_path=CKPT_PATH)
print("Model ready.")

TIPS = """
### Tips for best accuracy
- **Bright light on your face** (face a window or lamp — not backlit)
- **Look at the camera**, face filling the frame, roughly eye-level
- **Articulate a little more deliberately** than normal
- Leave a **~1 second pause between sentences**; keep each sentence ≥ ~1s
- It reads **lips only** — sound is never used
"""


def run(video, flip):
    if not video:
        return "Please record or upload a video first.", ""
    try:
        out = READER.transcribe(video, nbest=5, hflip=bool(flip))
    except Exception:
        return f"Error:\n{traceback.format_exc()}", ""
    if not out["segments"]:
        return ("No face / no speech detected. Try better lighting and face the "
                "camera."), ""
    # per-utterance breakdown
    lines = []
    for r in out["segments"]:
        if not r["text"]:
            continue
        a, b = r["seg_time"]
        lines.append(f"[{a:4.1f}–{b:4.1f}s]  {r['text']}")
    breakdown = "\n".join(lines)
    return out["transcript"].strip() or "(nothing recognized)", breakdown


with gr.Blocks(title="Silent Lip Reader") as demo:
    gr.Markdown("# 👄 Silent Lip Reader\n"
                "Record yourself (or upload) — it reads your **lips only**, "
                "no sound used, and writes what you said.")
    with gr.Row():
        with gr.Column():
            video = gr.Video(sources=["webcam", "upload"],
                             label="Record (webcam) or upload a clip")
            flip = gr.Checkbox(
                value=False,
                label="Flip horizontally — only tick if the transcript comes out "
                      "as gibberish (some setups mirror the video)")
            btn = gr.Button("Read my lips", variant="primary")
            gr.Markdown(TIPS)
        with gr.Column():
            transcript = gr.Textbox(label="Transcript (lip-read)", lines=4)
            breakdown = gr.Textbox(label="Per-utterance breakdown", lines=10)

    btn.click(run, inputs=[video, flip], outputs=[transcript, breakdown])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
