"""Client verso il modello LLM locale (Qwen3-4B) servito su localhost.

Il modello gira come servizio separato dentro l'OS ed espone un endpoint
OpenAI-compatible (`/v1/chat/completions`), come fanno llama.cpp server,
Ollama e TensorRT-LLM. Qui lo interroghiamo con la sola libreria standard
(`urllib`), coerentemente con la filosofia offline-first e zero-dipendenze
di Jarvis Mini: la chiamata e' a 127.0.0.1, non esce dalla macchina.

Il client e' volutamente model-agnostic: parla il protocollo, non conosce
il modello. Sostituire Qwen con un altro modello (es. Minerva) significa
cambiare il file servito, non questo codice.
"""

import json
import re
import urllib.error
import urllib.request

from ..config import Config
from ..intents.models import Result, Source
from .base import LocalAI

# Alcuni modelli (es. Qwen3) possono emettere token di controllo che NON vanno
# letti ad alta voce: il blocco di ragionamento <think>...</think> e i blocchi
# di chiamata strumenti <tool_call>...</tool_call>. Li rimuoviamo, insieme a
# eventuali tag di controllo isolati rimasti (es. un <tool_call> senza corpo).
_STRIP_RE = re.compile(
    r"<think>.*?</think>|<tool_call>.*?</tool_call>|<tool_response>.*?</tool_response>",
    re.DOTALL,
)
_LONE_TAG_RE = re.compile(r"</?(?:think|tool_call|tool_response)>")


def _clean(text: str) -> str:
    """Toglie ragionamento e chiamate-strumento, lasciando solo la risposta."""
    text = _STRIP_RE.sub("", text)
    text = _LONE_TAG_RE.sub("", text)
    return text.strip()

# Persona e regole del cervello di bordo. Le risposte vengono lette via TTS
# mentre si guida, quindi devono essere brevi. Vincolo di sicurezza: il
# modello non esegue e non finge di eseguire comandi sul veicolo — quelli
# sono gestiti dagli intent/tool deterministici dell'agente.
SYSTEM_PROMPT = (
    "Sei GSOI, l'assistente di bordo dell'automobile. Rispondi sempre in "
    "italiano, in modo breve e chiaro: le tue risposte vengono lette ad alta "
    "voce mentre l'utente guida. Non inventare azioni sul veicolo e non "
    "dichiarare di aver eseguito comandi (volume, navigazione, telefono): "
    "quei comandi li esegue l'agente, non tu. I dati di bordo (OBD/CAN) sono "
    "in sola lettura. Se non conosci una risposta, dillo con sincerita'."
)


class LocalModelClient(LocalAI):
    def __init__(self, config: Config):
        self.config = config

    def ask(self, text: str) -> Result:
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": self.config.model_temperature,
            "max_tokens": self.config.model_max_tokens,
            "stream": False,
            # Qwen3 ragiona di default: per l'assistente di bordo vogliamo
            # risposte dirette e brevi (lette via TTS). Con llama-server avviato
            # in modalità Jinja (--jinja) questo disattiva il blocco <think>;
            # se il server lo ignora, ci pensa comunque _clean() a rimuoverlo.
            "chat_template_kwargs": {"enable_thinking": False},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.config.model_chat_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                req, timeout=self.config.model_timeout
            ) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            answer = _clean(body["choices"][0]["message"]["content"])
            # Una "risposta" fatta solo di punteggiatura (es. il '.' rimasto da
            # un <tool_call> vuoto) equivale a nessuna risposta.
            if not answer or not re.search(r"[0-9A-Za-zÀ-ÿ]", answer):
                raise ValueError("risposta vuota dal modello")
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            OSError,
            ValueError,
            KeyError,
            IndexError,
            json.JSONDecodeError,
        ) as exc:
            # Il modello non e' raggiungibile o ha risposto in modo inatteso:
            # segnaliamo l'insuccesso cosi' il router puo' ripiegare sul
            # server GSOI (se disponibile).
            return Result(
                text="Il modello locale non e' raggiungibile in questo momento.",
                success=False,
                source=Source.LOCAL_AI,
                data={"query": text, "backend": "local", "error": str(exc)},
            )

        return Result(
            text=answer,
            success=True,
            source=Source.LOCAL_AI,
            data={
                "query": text,
                "backend": "local",
                "model": self.config.model_name,
            },
        )
