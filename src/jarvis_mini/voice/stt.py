"""Riconoscimento vocale (voce -> testo).

  * MockSTT — legge da stdin (default, nessuna dipendenza).
  * VoskSTT — STT reale offline con Vosk dal microfono.

Attivare Vosk con:
    JARVIS_STT=vosk JARVIS_VOSK_MODEL=/path/vosk-model-it

Cattura audio (due backend):
  * "arecord" (DEFAULT) — usa il comando `arecord` (alsa-utils) via subprocess.
      Robusto: passa dal layer ALSA "plug"/PipeWire che ricampiona a 16 kHz,
      evitando i problemi di PortAudio+PipeWire. Device ALSA opzionale con
      JARVIS_ARECORD_DEVICE (es. "default", "plughw:0,0").
  * "sounddevice" — stream PortAudio (richiede il pacchetto `sounddevice`).
      Selezione device con JARVIS_AUDIO_DEVICE (indice o nome).
    Scegli il backend con JARVIS_STT_CAPTURE=arecord|sounddevice.
"""

import json
import os
import subprocess
import time

_CHUNK = 8000  # byte letti per volta (~0.25 s a 16 kHz, 16-bit, mono)


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
        self._warned = False  # stampa l'errore una sola volta
        self._capture = os.environ.get("JARVIS_STT_CAPTURE", "arecord")

    def _ensure_model(self):
        if self._model is None:
            from vosk import Model  # import pigro
            self._model = Model(self.model_path)

    def _err(self, exc, hint=""):
        if not self._warned:
            print(f"[STT:errore] {exc}")
            if hint:
                print(hint)
            self._warned = True
        time.sleep(3)  # evita il loop a raffica se il mic non si apre
        return ""

    def transcribe(self) -> str:
        if self._capture == "sounddevice":
            return self._via_sounddevice()
        return self._via_arecord()

    # --- Backend robusto: arecord (alsa-utils) ------------------------------
    def _via_arecord(self) -> str:
        try:
            from vosk import KaldiRecognizer
            self._ensure_model()
            cmd = ["arecord", "-q", "-f", "S16_LE",
                   "-r", str(self.samplerate), "-c", "1", "-t", "raw"]
            dev = os.environ.get("JARVIS_ARECORD_DEVICE")
            if dev:
                cmd += ["-D", dev]

            rec = KaldiRecognizer(self._model, self.samplerate)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL)
            self._warned = False
            try:
                while True:
                    data = proc.stdout.read(_CHUNK)
                    if not data:
                        return ""  # arecord terminato
                    if rec.AcceptWaveform(data):
                        text = json.loads(rec.Result()).get("text", "").strip()
                        if text:  # ignora i silenzi, torna solo con parole
                            return text
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=1)
                except Exception:
                    proc.kill()
        except FileNotFoundError:
            return self._err("'arecord' non trovato",
                             "[STT] installa alsa-utils: sudo apt install alsa-utils")
        except Exception as exc:
            return self._err(exc, "[STT] cattura audio fallita (arecord). "
                                  "Prova JARVIS_ARECORD_DEVICE=default. Riprovo ogni 3s...")

    # --- Backend alternativo: sounddevice (PortAudio) -----------------------
    def _via_sounddevice(self) -> str:
        try:
            import queue
            import sounddevice as sd
            from vosk import KaldiRecognizer

            self._ensure_model()
            q = queue.Queue()

            def cb(indata, frames, time_, status):
                q.put(bytes(indata))

            dev = os.environ.get("JARVIS_AUDIO_DEVICE") or None
            if dev is not None:
                try:
                    dev = int(dev)
                except ValueError:
                    pass
            rec = KaldiRecognizer(self._model, self.samplerate)
            with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,
                                   dtype="int16", channels=1, callback=cb,
                                   device=dev):
                self._warned = False
                while True:
                    data = q.get()
                    if rec.AcceptWaveform(data):
                        return json.loads(rec.Result()).get("text", "").strip()
        except Exception as exc:
            return self._err(exc, "[STT] PortAudio non apre il mic. "
                                  "Prova il backend arecord (JARVIS_STT_CAPTURE=arecord). "
                                  "Riprovo ogni 3s...")


def make_stt() -> STT:
    model = os.environ.get("JARVIS_VOSK_MODEL")
    if os.environ.get("JARVIS_STT") == "vosk" and model:
        return VoskSTT(model)
    return MockSTT()
