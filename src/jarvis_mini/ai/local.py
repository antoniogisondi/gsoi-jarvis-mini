"""AI locale di fallback (STUB per la v0.1).

Gestisce le richieste non riconosciute dagli intent quando il server non
e' raggiungibile. In una fase successiva qui verra' collegato un piccolo
modello locale quantizzato (es. GGUF via llama.cpp), leggero e adatto al
Raspberry Pi 5.
"""

from ..intents.models import Result, Source


class LocalAI:
    def ask(self, text: str) -> Result:
        return Result(
            text=(
                "[stub AI locale] Non ho un comando locale per questa "
                "richiesta e il server GSOI non e' raggiungibile."
            ),
            success=False,
            source=Source.LOCAL_AI,
            data={"query": text},
        )
