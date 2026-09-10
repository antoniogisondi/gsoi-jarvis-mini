"""Compatibilita': il cervello locale e' stato scomposto in piu' moduli.

  * base.py         -> interfaccia LocalAI + factory make_local_ai
  * mock.py         -> MockLocalAI (nessun modello, sviluppo)
  * model_client.py -> LocalModelClient (Qwen3-4B via localhost)

Questo modulo resta come punto di import stabile.
"""

from .base import LocalAI, make_local_ai
from .mock import MockLocalAI
from .model_client import LocalModelClient

__all__ = ["LocalAI", "MockLocalAI", "LocalModelClient", "make_local_ai"]
