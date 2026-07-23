# HTTP API

This network interface wraps `python_api` for Swift and other non-Python
clients. It is the initial distribution boundary for the macOS and iOS
applications: Apple clients handle capture and presentation while the hosted
service performs preprocessing and inference.

```bash
pip install -r apis/http_api/requirements.txt
uvicorn apis.http_api.app:app --host 0.0.0.0 --port 8000
```

Submit a video:

```bash
curl -X POST http://127.0.0.1:8000/v1/transcriptions \
  -F video=@sample.mp4 \
  -F hflip=false
```

`POST /v1/transcriptions` is consumption-only. The uploaded file is used for
that transcription request and removed from temporary server storage
afterward. The endpoint does not register the clip as a dataset example or
authorize its use for training.

Future personalization may add separate authenticated endpoints for prompted
recordings, corrected transcripts, dataset status, training jobs, and model
selection. Those endpoints need explicit consent, user-scoped storage,
retention and deletion controls, and provenance linking each recording to its
exact prompt and recording session. They should not reuse the transcription
endpoint as an implicit data-collection channel.

The development server has no authentication. Add authentication, TLS, rate
limits, and deployment-specific upload limits before exposing it publicly.

See [`apps/apple/README.md`](../../apps/apple/README.md) for the planned macOS
and iOS client boundary.
