"""Assemblaggio dell'agente Jarvis Mini.

JarvisMini collega insieme motore intenti, tool locali, gestore della
connettivita', client remoto e AI locale dietro un'unica interfaccia
`handle(testo) -> Result`. E' il punto d'ingresso usato sia dalla CLI di
test sia dalla modalita' servizio (systemd).
"""

from typing import Optional

from .ai.local import LocalAI
from .config import Config
from .connectivity.mode_manager import Mode, ModeManager
from .intents.engine import IntentEngine
from .intents.models import Result
from .remote.client import RemoteClient
from .router.router import Router
from .tools.registry import build_default_registry


class JarvisMini:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()

        self.engine = IntentEngine()
        self.registry = build_default_registry()
        self.mode_manager = ModeManager(self.config)
        self.remote = RemoteClient(self.config)
        self.local_ai = LocalAI()

        self.router = Router(
            self.engine,
            self.registry,
            self.mode_manager,
            self.remote,
            self.local_ai,
        )

    def handle(self, text: str) -> Result:
        return self.router.handle(text)

    def mode(self) -> Mode:
        return self.mode_manager.current_mode()
