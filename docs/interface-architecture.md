# Interface and package architecture

Open-Altergo has two installable Python packages and one application today.

```text
apps/gradio/
    app.py
packages/silent_speech/
    pyproject.toml
    src/silent_speech/
cloud/engine/
    pyproject.toml
    src/open_altergo_engine/
training/
    prepare_dataset.py
    train_personal.py
    personalization.py
cloud/modal/
    app.py
```

`open_altergo_engine` owns Auto-AVSR preprocessing, model construction,
decoding, and training primitives. `silent_speech` owns the stable,
interface-neutral service contract. `apps/gradio` is only a presentation
adapter. `training` contains runnable workflows, while `cloud/modal` provisions
and invokes those workflows.

## Core API

```python
from silent_speech import RuntimeConfig, SilentSpeechService

service = SilentSpeechService(
    RuntimeConfig(
        device="cpu",
        detector="mediapipe",
        checkpoint_path="models/personalized_model.pt",
    )
)
result = service.transcribe("sample.mp4", hflip=False)
print(result["transcript"])
```

Creating the service does not load a checkpoint. The first transcription loads
it once. Separate initialization and inference locks prevent duplicate model
loads and concurrent mutation of decoder state.

When installed outside the checkout, set `OPEN_ALTERGO_ROOT` to a checkout that
contains `cloud/engine`, or install and run both editable packages from the
repository:

```bash
pip install -e cloud/engine -e packages/silent_speech
```

## Gradio

```bash
pip install -r apps/gradio/requirements.txt
python app.py
```

The root `app.py` remains the Hugging Face Spaces entry point. The actual UI
lives at `apps/gradio/app.py`; the core package never imports Gradio.

## Adding Swift

A Swift interface should call the same transcription contract through a small
HTTP or WebSocket adapter. This preserves a single Python preprocessing and
decoding implementation while iOS and macOS own capture and presentation.

On-device Swift inference is a separate track. It requires exporting the visual
frontend, Conformer, and decoder to an Apple-supported runtime and porting the
mouth-alignment preprocessing pipeline.
