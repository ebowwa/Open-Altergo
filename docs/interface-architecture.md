# Interface architecture

The model pipeline and the user interface are separate packages. Interfaces
depend on the core service; the core never imports Gradio.

```text
app.py                                  compatibility launcher
silent_speech/
├── core/
│   ├── config.py                       shared runtime configuration
│   └── service.py                      lazy, thread-safe inference API
└── interfaces/
    └── gradio_app.py                   Gradio components and formatting
engine/                                 existing Auto-AVSR implementation
```

## Core API

Any Python interface can use the same service:

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

Creating the service does not load the checkpoint. The first transcription
loads it once. Model initialization and inference are protected by separate
locks so multiple interface requests cannot create duplicate models or share
mutable decoder state concurrently.

## Gradio adapter

The Hugging Face-compatible launcher remains:

```bash
python app.py
```

The packaged entrypoint is equivalent:

```bash
python -m silent_speech.interfaces.gradio_app
```

Install only the core dependencies when no browser interface is needed:

```bash
pip install -r requirements-core.txt
```

Install the Gradio interface dependencies with:

```bash
pip install -r requirements-gradio.txt
```

`requirements.txt` continues to install the Gradio interface for Hugging Face
Spaces compatibility.

## Adding Swift

A Swift client should not reproduce Gradio behavior. Add a separate HTTP or
WebSocket adapter that calls `SilentSpeechService`, then have the iOS/macOS app
send video frames or clips to that adapter. This preserves one transcription
contract across Gradio and Swift.

On-device Swift inference is a separate deployment track. It would require
exporting the visual frontend, Conformer, and decoder to an Apple-compatible
runtime and replacing the Python preprocessing path.
