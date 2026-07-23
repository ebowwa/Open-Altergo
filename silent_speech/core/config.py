"""Runtime configuration shared by every user interface."""

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Model configuration with no dependency on a particular UI."""

    device: str = "cpu"
    detector: str = "mediapipe"
    checkpoint_path: str | None = None
    enhance: bool = True

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "RuntimeConfig":
        values = os.environ if environ is None else environ
        return cls(
            device=values.get("LIPREAD_DEVICE", "cpu"),
            detector=values.get("LIPREAD_DETECTOR", "mediapipe"),
            checkpoint_path=values.get("LIPREAD_CKPT") or None,
        )
