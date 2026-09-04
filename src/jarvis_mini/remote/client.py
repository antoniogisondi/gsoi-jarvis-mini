"""Client verso gsoi-jarvis (STUB per la v0.1).

Nella v0.1 il client non effettua chiamate reali: restituisce una risposta
segnaposto. In una fase successiva qui verra' implementata la vera chiamata
HTTP al server GSOI, che a sua volta interroga gsoi-llm.
"""

from ..config import Config
from ..intents.models import Result, Source


class RemoteClient:
    def __init__(self, config: Config):
        self.config = config

    def ask(self, text: str) -> Result:
        return Result(
            text=(
                "[stub server] La richiesta verrebbe inoltrata a "
                f"gsoi-jarvis ({self.config.server_url}) e quindi a gsoi-llm."
            ),
            success=True,
            source=Source.REMOTE,
            data={"forwarded": text},
        )
