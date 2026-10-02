"""Riconoscimento vocale (voce -> testo).

  * MockSTT — legge da stdin (default, nessuna dipendenza).
  * VoskSTT — STT reale offline con Vosk dal microfono.

Attivare Vosk con:
    JARVIS_STT=vosk JARVIS_VOSK_MODEL=/path/vosk-model-it

Cattura audio (due backend):
  * "arecord" (DEFAULT) — usa `arecord` (alsa-utils) via subprocess, tenendo
      UN SOLO processo aperto per tutta la sessione: su schede HDA il device
      che converte a 16 kHz e' spesso solo `plughw:0,0`, ed e' ESCLUSIVO —
      aprendolo/chiudendolo a ogni frase, PipeWire lo "ruba" nel frattempo.
      Tenendolo aperto il device resta nostro; l'audio accumulato mentre il
      cervello elabora viene scartato (drain) prima di riascoltare.
      Device ALSA con JARVIS_ARECORD_DEVICE (default: plughw:0,0).
  * "sounddevice" — stream PortAudio (JARVIS_STT_CAPTURE=sounddevice,
      device con JARVIS_AUDIO_DEVICE). Fragile con PipeWire.
"""

import json
import os
import select
import subprocess
import time

_CHUNK = 4000  # byte letti per volta (~0.12 s a 16 kHz, 16-bit, mono)


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
        self._proc = None       # processo arecord persistente
        self._warned = False

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
        time.sleep(3)
        return ""

    def transcribe(self) -> str:
        if os.environ.get("JARVIS_STT_CAPTURE") == "sounddevice":
            return self._via_sounddevice()
        return self._via_arecord()

    # --- Backend robusto: UN arecord persistente ----------------------------
    def _start_arecord(self):
        dev = os.environ.get("JARVIS_ARECORD_DEVICE", "plughw:0,0")
        cmd = ["arecord", "-q", "-f", "S16_LE",
               "-r", str(self.samplerate), "-c", "1", "-t", "raw", "-D", dev]
        self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL)

    def _drain(self, fd):
        """Scarta l'audio bufferizzato (es. accumulato durante l'elaborazione)."""
        while select.select([fd], [], [], 0)[0]:
            if not os.read(fd, 65536):
                break

    def _via_arecord(self) -> str:
        try:
            from vosk import KaldiRecognizer
            self._ensure_model()

            if self._proc is None or self._proc.poll() is not None:
                self._start_arecord()
                time.sleep(0.3)  # lascia aprire il device
                if self._proc.poll() is not None:
                    return self._err("arecord non si avvia",
                                     "[STT] device occupato? Prova "
                                     "JARVIS_ARECORD_DEVICE=plughw:0,0. Riprovo ogni 3s...")

            fd = self._proc.stdout.fileno()
            self._drain(fd)                      # butta il backlog
            rec = KaldiRecognizer(self._model, self.samplerate)
            self._warned = False
            while True:
                r = select.select([fd], [], [], 1.0)[0]
                if not r:
                    continue
                data = os.read(fd, _CHUNK)
                if not data:                     # arecord e' morto -> riavvia
                    self._proc = None
                    return ""
                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result()).get("text", "").strip()
                    if text:                     # ignora i silenzi
                        return text
        except FileNotFoundError:
            return self._err("'arecord' non trovato",
                             "[STT] installa alsa-utils: sudo apt install alsa-utils")
        except Exception as exc:
            self._proc = None
            return self._err(exc, "[STT] cattura audio fallita. Riprovo ogni 3s...")

    def close(self):
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=1)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

    def __del__(self):
        self.close()

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
                                  "Prova il backend arecord. Riprovo ogni 3s...")


def make_stt() -> STT:
    model = os.environ.get("JARVIS_VOSK_MODEL")
    if os.environ.get("JARVIS_STT") == "vosk" and model:
        return VoskSTT(model)
    return MockSTT()
