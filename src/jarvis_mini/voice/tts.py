"""Sintesi vocale (testo -> voce).

Due implementazioni:
  * MockTTS  — stampa soltanto (default, nessuna dipendenza).
  * PiperTTS — voce reale offline con Piper (binario + modello .onnx).

La factory sceglie in base alle variabili d'ambiente; se Piper non e'
disponibile ripiega sul mock, cosi' l'app funziona sempre.
"""

import os
import shutil
import subprocess
import tempfile


class TTS:
    def say(self, text: str) -> None:
        raise NotImplementedError


class MockTTS(TTS):
    def say(self, text: str) -> None:
        print(f"[TTS] {text}")


class PiperTTS(TTS):
    """Voce reale offline via Piper.

    Richiede il binario `piper`, un modello voce (.onnx) e un player audio
    (`aplay`). Attivare con:
        JARVIS_TTS=piper JARVIS_PIPER_MODEL=/path/voice.onnx
    """

    def __init__(self, model: str, piper_bin: str = "piper", player: str = "aplay"):
        self.model = model
        self.piper_bin = piper_bin
        self.player = player

    def say(self, text: str) -> None:
        wav = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav = f.name
            subprocess.run(
                [self.piper_bin, "--model", self.model, "--output_file", wav],
                input=text.encode("utf-8"),
                check=True,
            )
            subprocess.run([self.player, wav], check=False)
        except Exception as exc:  # non deve mai far cadere l'agente
            print(f"[TTS:fallback] {text}  ({exc})")
        finally:
            if wav:
                try:
                    os.unlink(wav)
                except OSError:
                    pass


def make_tts() -> TTS:
    model = os.environ.get("JARVIS_PIPER_MODEL")
    if os.environ.get("JARVIS_TTS") == "piper" and model and shutil.which("piper"):
        return PiperTTS(model)
    return MockTTS()
