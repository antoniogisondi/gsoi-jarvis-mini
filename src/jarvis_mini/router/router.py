"""Router interno di Jarvis Mini — cervello 100% a bordo.

    richiesta utente
    -> comando semplice (intent locale con tool)? -> tool locale (deterministico)
    -> altrimenti                                 -> cervello LOCALE (LLM su localhost)

La richiesta NON esce mai dalla macchina: non esiste un modello sul server,
nessun round-trip di rete. I comandi semplici restano sempre locali e
deterministici: non ha senso — ne' e' sicuro — far passare "alza il volume"
o "che temperatura ha il motore?" attraverso un LLM.

La connettivita' Internet (vedi ModeManager) non riguarda il cervello: serve
solo alle funzioni che richiedono la rete (traffico, meteo, OTA).
"""

from typing import Dict

from ..ai.base import LocalAI
from ..intents.engine import IntentEngine
from ..intents.models import Intent, Result
from ..tools.base import Tool


class Router:
    def __init__(
        self,
        engine: IntentEngine,
        registry: Dict[Intent, Tool],
        local_ai: LocalAI,
    ):
        self.engine = engine
        self.registry = registry
        self.local_ai = local_ai

    def handle(self, text: str) -> Result:
        match = self.engine.recognize(text)
        tool = self.registry.get(match.intent)

        # Comando semplice: intent locale riconosciuto con tool associato.
        if match.intent is not Intent.UNKNOWN and tool is not None:
            return tool.execute(match)

        # Tutto il resto lo gestisce il cervello LOCALE.
        return self.local_ai.ask(text)
