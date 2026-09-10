"""Interfaccia del 'cervello a bordo' (AI locale) e relativa factory.

Nel modello architetturale attuale il cervello gira DENTRO l'auto: un LLM
locale (Qwen3-4B-Instruct) servito come processo separato su localhost.
Interrogarlo non passa dalla rete, quindi la latenza client-server sparisce.

Questo modulo definisce l'interfaccia comune `LocalAI` e sceglie
l'implementazione in base alla configurazione (env `JARVIS_AI`):

  * "mock"  -> MockLocalAI       (default: sviluppo senza modello/hardware)
  * "local" -> LocalModelClient  (client OpenAI-compatible verso 127.0.0.1)

Il resto del codice (router, agente) dipende solo da questa interfaccia:
cambiare o aggiornare il modello non richiede modifiche a Jarvis Mini.
"""

import abc
from typing import Optional

from ..config import Config
from ..intents.models import Result


class LocalAI(abc.ABC):
    """Cervello locale: risponde alle richieste non gestite dagli intent."""

    @abc.abstractmethod
    def ask(self, text: str) -> Result:
        """Elabora una richiesta in linguaggio naturale e restituisce un Result.

        `success=False` segnala che il cervello non ha potuto rispondere
        (modello non attivo/irraggiungibile): il router puo' allora ripiegare
        sul server GSOI, se disponibile.
        """
        raise NotImplementedError


def make_local_ai(config: Optional[Config] = None) -> LocalAI:
    """Costruisce l'implementazione di AI locale scelta dalla config/env."""
    config = config or Config.from_env()
    backend = (config.ai_backend or "mock").strip().lower()

    if backend in ("local", "model", "llm", "qwen", "llama"):
        from .model_client import LocalModelClient
        return LocalModelClient(config)

    from .mock import MockLocalAI
    return MockLocalAI()
