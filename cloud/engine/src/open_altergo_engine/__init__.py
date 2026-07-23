"""Auto-AVSR inference and training engine for Open-Altergo."""

__all__ = ["LipReader"]


def __getattr__(name):
    if name == "LipReader":
        from .pipeline import LipReader

        return LipReader
    raise AttributeError(name)
