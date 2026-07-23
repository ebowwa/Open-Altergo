# Open-Altergo engine

This installable package owns the Auto-AVSR model, preprocessing, decoding, and
training primitives. Applications and training workflows depend on it; it does
not depend on Gradio or Modal.

From the repository root:

```bash
pip install -e cloud/engine
python -m open_altergo_engine.local_infer sample.mp4
```
