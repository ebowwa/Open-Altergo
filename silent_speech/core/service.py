"""Stable service API around the existing Auto-AVSR inference engine."""

import sys
import threading
from pathlib import Path
from typing import Any, Callable, Protocol

from .config import RuntimeConfig


Transcription = dict[str, Any]


class ReaderBackend(Protocol):
    """Backend contract implemented by the current Auto-AVSR LipReader."""

    def transcribe(
        self,
        path: str,
        nbest: int = 5,
        hflip: bool = False,
        max_seconds: int = 40,
    ) -> Transcription: ...

    def transcribe_auto(
        self,
        path: str,
        nbest: int = 5,
        max_seconds: int = 40,
    ) -> Transcription: ...


ReaderFactory = Callable[[RuntimeConfig], ReaderBackend]


def _legacy_reader_factory(config: RuntimeConfig) -> ReaderBackend:
    """Load the original engine without exposing its path setup to interfaces."""

    project_root = Path(__file__).resolve().parents[2]
    for vendor_name in ("face_detection", "face_alignment"):
        vendor_path = project_root / "vendor" / vendor_name
        if vendor_path.is_dir() and str(vendor_path) not in sys.path:
            sys.path.insert(0, str(vendor_path))

    engine_path = project_root / "engine"
    if str(engine_path) not in sys.path:
        sys.path.insert(0, str(engine_path))

    from pipeline import LipReader

    return LipReader(
        device=config.device,
        detector=config.detector,
        enhance=config.enhance,
        ckpt_path=config.checkpoint_path,
    )


class SilentSpeechService:
    """Lazy, interface-neutral access to lip-reading inference.

    Model creation and inference are locked separately. This prevents duplicate
    model loads during concurrent startup and avoids sharing mutable decoder
    state across simultaneous requests.
    """

    def __init__(
        self,
        config: RuntimeConfig | None = None,
        reader_factory: ReaderFactory | None = None,
    ):
        self.config = config or RuntimeConfig.from_env()
        self._reader_factory = reader_factory or _legacy_reader_factory
        self._reader: ReaderBackend | None = None
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._reader is not None

    @property
    def reader(self) -> ReaderBackend:
        if self._reader is None:
            with self._load_lock:
                if self._reader is None:
                    self._reader = self._reader_factory(self.config)
        return self._reader

    def transcribe(
        self,
        video_path: str | Path,
        *,
        nbest: int = 5,
        hflip: bool = False,
        max_seconds: int = 40,
    ) -> Transcription:
        if not video_path:
            raise ValueError("video_path is required")
        with self._inference_lock:
            return self.reader.transcribe(
                str(video_path),
                nbest=nbest,
                hflip=hflip,
                max_seconds=max_seconds,
            )

    def transcribe_auto(
        self,
        video_path: str | Path,
        *,
        nbest: int = 5,
        max_seconds: int = 40,
    ) -> Transcription:
        if not video_path:
            raise ValueError("video_path is required")
        with self._inference_lock:
            return self.reader.transcribe_auto(
                str(video_path),
                nbest=nbest,
                max_seconds=max_seconds,
            )
