# HTTP API

This network interface wraps `python_api` for Swift and other non-Python
clients.

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

The development server has no authentication. Add authentication, TLS, rate
limits, and deployment-specific upload limits before exposing it publicly.
