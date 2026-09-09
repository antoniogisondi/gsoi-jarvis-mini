"""Motore proattivo: 'anticipare nelle piccole cose'.

Non e' un LLM: e' logica a regole/eventi che osserva la telemetria e, quando
serve, propone/avvisa (mostrato sul cockpit come striscia Agent e detto a
voce via TTS).
"""

from .rules import Suggestion, DEFAULT_RULES
from .engine import ProactiveEngine

__all__ = ["Suggestion", "DEFAULT_RULES", "ProactiveEngine"]
