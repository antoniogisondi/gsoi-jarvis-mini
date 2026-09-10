"""Router interno di Jarvis Mini.

Implementa la logica di instradamento del progetto (cervello a bordo):

    richiesta utente
    -> comando semplice (intent locale con tool)?
       -> si': esegui il tool locale (deterministico, sempre in locale)
       -> no:  interroga il cervello LOCALE (LLM Qwen3-4B su localhost)
               -> ha risposto?         -> restituisci la risposta locale
               -> non e' raggiungibile -> server GSOI disponibile?
                                          -> si': inoltra al server (fallback)
                                          -> no:  restituisci l'esito locale

Con il modello in esecuzione a bordo la richiesta NON esce mai dalla
macchina: nessun round-trip di rete, latenza minima. Il server GSOI resta
un fallback opzionale (usato solo se il modello locale non e' disponibile).

I comandi semplici restano sempre locali e deterministici: non ha senso —
ne' e' sicuro — far passare "alza il volume" o "che temperatura ha il
motore?" attraverso un LLM.
"""

from typing import Dict

from ..ai.base import LocalAI
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

        # Richiesta complessa / non riconosciuta: prima il cervello LOCALE.
        result = self.local_ai.ask(text)
        if result.success:
            return result

        # Il modello locale non e' disponibile: fallback opzionale al server.
        if self.mode_manager.is_server_available():
            return self.remote_client.ask(text)

        return result
