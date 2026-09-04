"""Riconoscimento degli intenti (offline)."""

from .models import Intent, IntentMatch, Result, Source
from .engine import IntentEngine

__all__ = ["Intent", "IntentMatch", "Result", "Source", "IntentEngine"]
