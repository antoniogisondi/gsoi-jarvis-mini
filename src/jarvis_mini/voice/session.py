"""Sessione di conversazione vocale: il "cuore" dell'assistente.

Un unico oggetto condiviso raccoglie lo stato vivo del dialogo (chi ha
parlato, cosa ha risposto Jarvis, in che fase siamo) ed espone un solo
metodo, `ask(text)`, usato da TRE sorgenti d'ingresso diverse:

  * il loop microfono (wake word -> STT -> ask -> TTS), quando c'e' l'hardware;
  * l'endpoint HTTP `POST /ask`, per pilotare l'assistente a testo (utile in
    QEMU/sviluppo, dove non c'e' microfono, e come "premi per parlare" del
    cockpit);
  * eventuali test.

Lo stato ricavato (`to_dict()`) viene incluso in `/state`, cosi' il cockpit
mostra il dialogo dal vivo (fase e ultime battute) senza logica propria.

Tutto e' thread-safe (un lock serializza le richieste: l'assistente gestisce
una conversazione alla volta) e senza dipendenze esterne.
"""

import threading
import time
from typing import Callable, List, Optional

from ..intents.models import Result

# Fasi dell'assistente, lette dalla UI per animare l'orb.
STATE_IDLE = "idle"
STATE_LISTENING = "listening"   # in ascolto dopo la wake word
STATE_THINKING = "thinking"     # STT ok, il cervello sta elaborando
STATE_SPEAKING = "speaking"     # sta pronunciando la risposta

_MAX_HISTORY = 12  # battute conservate (utente + Jarvis), le piu' recenti


class VoiceSession:
    """Stato vivo della conversazione + punto d'ingresso unico `ask()`."""

    def __init__(self, agent, max_history: int = _MAX_HISTORY):
        self._agent = agent
        self._max_history = max_history
        self._lock = threading.Lock()

        self._state = STATE_IDLE
        self._last_user = ""
        self._last_reply = ""
        self._history: List[dict] = []  # [{"role": "you"|"jarvis", "text": str, "ts": float}]

    # -- fasi -----------------------------------------------------------------
    def set_state(self, state: str) -> None:
        """Aggiorna la fase (usato dal loop microfono, es. 'listening')."""
        with self._lock:
            self._state = state

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    def _record(self, role: str, text: str) -> None:
        self._history.append({"role": role, "text": text, "ts": time.time()})
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

    # -- ingresso unico -------------------------------------------------------
    def ask(self, text: str, speak: bool = True) -> Result:
        """Gestisce una battuta dell'utente: cervello -> (voce) -> risposta.

        Serializzata: una conversazione alla volta. Non solleva mai
        (l'assistente non deve "cadere" per una richiesta malformata):
        in caso di errore restituisce un Result d'errore parlato.
        """
        text = (text or "").strip()
        if not text:
            return Result(text="", success=False)

        with self._lock:
            self._state = STATE_THINKING
            self._last_user = text
            self._record("you", text)
            try:
                result = self._agent.handle(text)
            except Exception as exc:  # il cervello non deve mai fermare l'assistente
                result = Result(text="Scusa, non sono riuscito a elaborare la richiesta.",
                                success=False)
                print(f"[voce:ask:errore] {exc}")

            self._last_reply = result.text
            self._record("jarvis", result.text)
            self._state = STATE_SPEAKING

        # La sintesi vocale avviene FUORI dal lock (puo' essere lenta) ma dopo
        # aver gia' pubblicato la risposta: la UI la mostra subito.
        if speak and result.text:
            try:
                self._agent.say(result.text)
            except Exception as exc:
                print(f"[voce:tts:errore] {exc}")

        with self._lock:
            # Torna in idle solo se nessun'altra richiesta ha cambiato fase.
            if self._state == STATE_SPEAKING:
                self._state = STATE_IDLE
        return result

    # -- vista per /state -----------------------------------------------------
    def to_dict(self) -> dict:
        """Istantanea per il cockpit: fase + ultime battute + storia recente."""
        with self._lock:
            return {
                "state": self._state,
                "listening": self._state != STATE_IDLE,
                "you": self._last_user,
                "reply": self._last_reply,
                "history": list(self._history),
            }


def make_ask_handler(session: VoiceSession) -> Callable[[str], Result]:
    """Handler per l'endpoint HTTP `POST /ask`."""
    def _handler(text: str) -> Result:
        return session.ask(text)
    return _handler
