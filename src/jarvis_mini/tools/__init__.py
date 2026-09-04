"""Tool locali dell'automobile (implementazioni mock per la v0.1)."""

from .base import Tool
from .registry import build_default_registry

__all__ = ["Tool", "build_default_registry"]
