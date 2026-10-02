"""Riconoscimento vocale (voce -> testo).

  * MockSTT — legge da stdin (default, nessuna dipendenza).
  * VoskSTT — STT reale offline con Vosk dal microfono.

Attivare Vosk con:
    JARVIS_STT=vosk JARVIS_VOSK_MODEL=/path/vosk-model-it
Richiede i pacchetti `vosk` e `sounddevice` (audio ALSA).

Scelta del microfono (se il default non si apre, es. PipeWire/ALSA):
    JARVIS_AUDIO_DEVICE=pulse     # oppure l'indice numerico da
                                  #   python -c "import sounddevice as sd; print(sd.query_devices())"
"""

import json
import os
import time


class STT:
    def transcribe(self) -> str:
        raise NotImplementedError


class MockSTT(STT):
    def transcribe(self) -> str:
        try:
            return input("(parla) > ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""


def _audio_device():
    """Device d'ingresso scelto via env (indice numerico o nome); None = default."""
    dev = os.environ.get("JARVIS_AUDIO_DEVICE")
    if dev is None or dev == "":
        return None
    try:
        return int(dev)
    except ValueError:
        return dev  # nome, es. "pulse"


class VoskSTT(STT):
    def __init__(self, model_path: str, samplerate: int = 16000):
        self.model_path = model_path
        self.samplerate = samplerate
        self._model = None
        self._warned = False  # per non inondare il log con lo stesso errore

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
                                   dtype="int16", channels=1, callback=cb,
                                   device=_audio_device()):
                self._warned = False
                while True:
                    data = q.get()
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        return res.get("text", "").strip()
        except Exception as exc:
            # Stampa l'errore UNA volta sola e rallenta: senza questo, se il
            # microfono non si apre il loop vocale riprova a raffica (100% CPU).
            if not self._warned:
                print(f"[STT:errore] {exc}")
                print("[STT] microfono non disponibile: controlla 'arecord -l' e "
                      "JARVIS_AUDIO_DEVICE. Riprovo ogni 3s...")
                self._warned = True
            time.sleep(3)
            return ""


def make_stt() -> STT:
    model = os.environ.get("JARVIS_VOSK_MODEL")
    if os.environ.get("JARVIS_STT") == "vosk" and model:
        return VoskSTT(model)
    return MockSTT()
