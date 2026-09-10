"""Cervello a bordo (AI locale): interfaccia, mock e client del modello LLM."""

from .base import LocalAI, make_local_ai
from .mock import MockLocalAI
from .model_client import LocalModelClient

__all__ = ["LocalAI", "MockLocalAI", "LocalModelClient", "make_local_ai"]
