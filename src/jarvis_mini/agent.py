"""Assemblaggio dell'agente Jarvis Mini.

JarvisMini collega motore intenti, tool locali, cervello locale (LLM) e
gestore della connettivita' dietro un'unica interfaccia
`handle(testo) -> Result`. E' il punto d'ingresso usato sia dalla CLI di
test sia dalla modalita' servizio (systemd).

Il cervello e' sempre a bordo: non esiste un modello sul server. La
connettivita' serve solo per le funzioni online (traffico, meteo, OTA).
"""

from typing import Optional

from .ai.base import make_local_ai
from .config import Config
from .connectivity.mode_manager import Mode, ModeManager
from .intents.engine import IntentEngine
from .intents.models import Result
from .router.router import Router
from .tools.registry import build_default_registry
from .voice.tts import make_tts


class JarvisMini:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()

        self.engine = IntentEngine()
        self.registry = build_default_registry()
        # Stato della rete (per le funzioni online), non per il cervello.
        self.mode_manager = ModeManager(self.config)
        # Cervello a bordo: mock di default, LLM locale con JARVIS_AI=local.
        self.local_ai = make_local_ai(self.config)
        self.tts = make_tts()

        self.router = Router(self.engine, self.registry, self.local_ai)

    def say(self, text: str) -> None:
        """Pronuncia un testo via TTS (mock nella v0.1)."""
        self.tts.say(text)

    def handle(self, text: str) -> Result:
        return self.router.handle(text)

    def mode(self) -> Mode:
        """Stato della rete: CONNECTED se c'e' Internet, altrimenti OFFLINE."""
        return self.mode_manager.current_mode()
