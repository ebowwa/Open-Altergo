# Interface and API architecture

Open-Altergo separates direct Python calls from network access:

```text
apps/gradio/
    app.py
apis/python_api/
    pyproject.toml
    src/
        __init__.py
        core/
apis/http_api/
    app.py
cloud/engine/
    pyproject.toml
    src/open_altergo_engine/
training/
cloud/modal/
```

## Python API

`python_api` is the in-process interface. Gradio and the HTTP server import it
directly:

```python
from python_api import RuntimeConfig, SilentSpeechService

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

Install the direct API and engine:

```bash
pip install -e cloud/engine -e apis/python_api
```

## HTTP API

The HTTP API is a real network boundary for Swift, remote programs, and other
languages:

```bash
pip install -r apis/http_api/requirements.txt
uvicorn apis.http_api.app:app --host 0.0.0.0 --port 8000
```

Endpoints:

- `GET /health` reports process and lazy-model state.
- `POST /v1/transcriptions` accepts a multipart video plus `hflip`, `nbest`,
  and `max_seconds`.

Uploaded files are capped at 250 MB and removed after each request. The
development server intentionally has no authentication; a public deployment
still needs TLS, authentication, rate limits, and deployment-level request
limits.

## Gradio

```bash
pip install -r apps/gradio/requirements.txt
python app.py
```

The root `app.py` remains the Hugging Face Spaces entry point. The actual UI
lives at `apps/gradio/app.py` and imports `python_api`.

## Swift

Swift calls the HTTP API; it does not embed the Python API:

```text
Swift ──HTTP──► http_api ──direct call──► python_api ──► engine
```

On-device Swift inference remains a separate track requiring model export and a
native port of mouth-alignment preprocessing.
