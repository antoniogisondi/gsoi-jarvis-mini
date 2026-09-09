"""Riconoscimento vocale (voce -> testo).

  * MockSTT — legge da stdin (default, nessuna dipendenza).
  * VoskSTT — STT reale offline con Vosk dal microfono.

Attivare Vosk con:
    JARVIS_STT=vosk JARVIS_VOSK_MODEL=/path/vosk-model-it
Richiede i pacchetti `vosk` e `sounddevice` (audio ALSA).
"""

import json
import os


class STT:
    def transcribe(self) -> str:
        raise NotImplementedError


class MockSTT(STT):
    def transcribe(self) -> str:
        try:
            return input("(parla) > ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""


class VoskSTT(STT):
    def __init__(self, model_path: str, samplerate: int = 16000):
        self.model_path = model_path
        self.samplerate = samplerate
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            from vosk import Model  # import pigro
            self._model = Model(self.model_path)

    def transcribe(self) -> str:
        try:
            import queue
            import sounddevice as sd
            from vosk import KaldiRecognizer

            self._ensure_model()
            q = queue.Queue()

            def cb(indata, frames, time_, status):
                q.put(bytes(indata))

            rec = KaldiRecognizer(self._model, self.samplerate)
            with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,
                                   dtype="int16", channels=1, callback=cb):
                while True:
                    data = q.get()
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        return res.get("text", "").strip()
        except Exception as exc:
            print(f"[STT:errore] {exc}")
            return ""


def make_stt() -> STT:
    model = os.environ.get("JARVIS_VOSK_MODEL")
    if os.environ.get("JARVIS_STT") == "vosk" and model:
        return VoskSTT(model)
    return MockSTT()
