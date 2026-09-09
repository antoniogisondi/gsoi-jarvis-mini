"""Rilevamento della wake word ("Hey GSOI").

  * MockWakeWord    — non ascolta (default).
  * OpenWakeWordDet — reale offline con openWakeWord dal microfono.

Attivare con:
    JARVIS_WAKEWORD=oww JARVIS_OWW_MODEL=/path/hey_gsoi.onnx
Richiede `openwakeword` e `sounddevice`.
"""

import os


class WakeWord:
    def wait(self) -> bool:
        raise NotImplementedError


class MockWakeWord(WakeWord):
    def wait(self) -> bool:
        return True


class OpenWakeWordDet(WakeWord):
    def __init__(self, model_path: str, threshold: float = 0.5, samplerate: int = 16000):
        self.model_path = model_path
        self.threshold = threshold
        self.samplerate = samplerate

    def wait(self) -> bool:
        try:
            import numpy as np
            import sounddevice as sd
            from openwakeword.model import Model

            model = Model(wakeword_models=[self.model_path])
            with sd.InputStream(samplerate=self.samplerate, channels=1,
                                dtype="int16", blocksize=1280) as stream:
                while True:
                    frame, _ = stream.read(1280)
                    scores = model.predict(np.frombuffer(frame, dtype=np.int16))
                    if any(v >= self.threshold for v in scores.values()):
                        return True
        except Exception as exc:
            print(f"[WakeWord:errore] {exc}")
            return True  # in errore, non bloccare il flusso


def make_wakeword() -> WakeWord:
    model = os.environ.get("JARVIS_OWW_MODEL")
    if os.environ.get("JARVIS_WAKEWORD") == "oww" and model:
        return OpenWakeWordDet(model)
    return MockWakeWord()
