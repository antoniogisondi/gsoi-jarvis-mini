"""Sintesi vocale (testo -> voce).

Implementazioni:
  * MockTTS   — stampa soltanto (default, nessuna dipendenza).
  * EspeakTTS — voce offline immediata via espeak-ng (robotica, nessun modello).
  * PiperTTS  — voce reale naturale offline con Piper (binario + modello .onnx).

La factory sceglie in base alle variabili d'ambiente; se il motore scelto non
e' disponibile ripiega sul mock, cosi' l'app funziona sempre.

  JARVIS_TTS=espeak   [JARVIS_ESPEAK_VOICE=it]  [JARVIS_ESPEAK_SPEED=160]
  JARVIS_TTS=piper     JARVIS_PIPER_MODEL=/path/voice.onnx
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


class EspeakTTS(TTS):
    """Voce offline immediata via espeak-ng (nessun modello da scaricare).

    Voce robotica ma funziona subito; in italiano con -v it. Attivare con:
        JARVIS_TTS=espeak  [JARVIS_ESPEAK_VOICE=it]  [JARVIS_ESPEAK_SPEED=160]
    """

    def __init__(self, binary: str = "espeak-ng", voice: str = "it", speed=None):
        self.binary = binary
        self.voice = voice
        self.speed = speed

    def say(self, text: str) -> None:
        try:
            cmd = [self.binary, "-v", self.voice]
            if self.speed:
                cmd += ["-s", str(self.speed)]
            cmd += ["--", text]
            subprocess.run(cmd, check=False)
        except Exception as exc:  # non deve mai far cadere l'agente
            print(f"[TTS:fallback] {text}  ({exc})")


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
    kind = os.environ.get("JARVIS_TTS")
    if kind == "piper":
        model = os.environ.get("JARVIS_PIPER_MODEL")
        if model and shutil.which("piper"):
            return PiperTTS(model)
    if kind == "espeak":
        binary = shutil.which("espeak-ng") or shutil.which("espeak")
        if binary:
            speed = os.environ.get("JARVIS_ESPEAK_SPEED")
            return EspeakTTS(binary=binary,
                             voice=os.environ.get("JARVIS_ESPEAK_VOICE", "it"),
                             speed=int(speed) if speed else None)
    return MockTTS()
