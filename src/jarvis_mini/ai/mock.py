"""AI locale MOCK: usata quando nessun modello locale e' in esecuzione.

Non inventa risposte. Segnala che il cervello a bordo non e' disponibile
(`success=False`), cosi' il router puo' eventualmente ripiegare sul server
GSOI (opzionale). E' l'implementazione di default per sviluppare senza il
Jetson e senza il modello.
"""

from ..intents.models import Result, Source
from .base import LocalAI


class MockLocalAI(LocalAI):
    def ask(self, text: str) -> Result:
        return Result(
            text=(
                "[AI locale non attiva] Nessun modello in esecuzione a bordo. "
                "Avvia il servizio del modello (Qwen3-4B su 127.0.0.1) e "
                "imposta JARVIS_AI=local."
            ),
            success=False,
            source=Source.LOCAL_AI,
            data={"query": text, "backend": "mock"},
        )
