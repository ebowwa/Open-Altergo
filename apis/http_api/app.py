"""HTTP interface for Open-Altergo transcription."""

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from python_api import RuntimeConfig, SilentSpeechService


MAX_UPLOAD_BYTES = 250 * 1024 * 1024
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm"}


def _video_suffix(filename):
    suffix = Path(filename or "").suffix.lower()
    return suffix if suffix in VIDEO_SUFFIXES else ".mp4"


async def _store_upload(upload):
    size = 0
    temporary = tempfile.NamedTemporaryFile(
        suffix=_video_suffix(upload.filename),
        delete=False,
    )
    path = Path(temporary.name)
    try:
        with temporary:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Video exceeds the 250 MB upload limit",
                    )
                temporary.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    if size == 0:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded video is empty")
    return path


def create_app(service=None):
    service = service or SilentSpeechService(RuntimeConfig.from_env())
    app = FastAPI(
        title="Open-Altergo HTTP API",
        version="0.1.0",
    )

    @app.get("/health")
    def health():
        return {"status": "ok", "model_loaded": service.is_loaded}

    @app.post("/v1/transcriptions")
    async def transcribe(
        video: UploadFile = File(...),
        hflip: bool = Form(False),
        nbest: int = Form(5),
        max_seconds: int = Form(40),
    ):
        if not 1 <= nbest <= 40:
            raise HTTPException(status_code=422, detail="nbest must be between 1 and 40")
        if not 1 <= max_seconds <= 120:
            raise HTTPException(
                status_code=422,
                detail="max_seconds must be between 1 and 120",
            )

        path = await _store_upload(video)
        try:
            return await run_in_threadpool(
                lambda: service.transcribe(
                    path,
                    nbest=nbest,
                    hflip=hflip,
                    max_seconds=max_seconds,
                )
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            path.unlink(missing_ok=True)

    return app


app = create_app()
