"""Router interno di Jarvis Mini.

Implementa la logica di instradamento del progetto:

    richiesta utente
    -> comando semplice (intent locale con tool)?
       -> si': esegui il tool locale (ANCHE se Internet e' disponibile)
       -> no:
          server GSOI disponibile?
          -> si': inoltra al server (gsoi-jarvis/gsoi-llm)
          -> no:  AI locale (fallback)

I comandi semplici restano sempre locali: non ha senso inviare al server
richieste come "alza il volume" o "che temperatura ha il motore?".
"""

from typing import Dict

from ..ai.local import LocalAI
from ..connectivity.mode_manager import ModeManager
from ..intents.engine import IntentEngine
from ..intents.models import Intent, Result
from ..remote.client import RemoteClient
from ..tools.base import Tool


class Router:
    def __init__(
        self,
        engine: IntentEngine,
        registry: Dict[Intent, Tool],
        mode_manager: ModeManager,
        remote_client: RemoteClient,
        local_ai: LocalAI,
    ):
        self.engine = engine
        self.registry = registry
        self.mode_manager = mode_manager
        self.remote_client = remote_client
        self.local_ai = local_ai

    def handle(self, text: str) -> Result:
        match = self.engine.recognize(text)
        tool = self.registry.get(match.intent)

        # Comando semplice: intent locale riconosciuto con tool associato.
        if match.intent is not Intent.UNKNOWN and tool is not None:
            return tool.execute(match)

        # Richiesta complessa / non riconosciuta localmente.
        if self.mode_manager.is_server_available():
            return self.remote_client.ask(text)

        return self.local_ai.ask(text)
