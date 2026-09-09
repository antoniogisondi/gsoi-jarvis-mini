"""Voce di Jarvis Mini: wake word, STT (voce->testo), TTS (testo->voce).

v0.1: interfacce + implementazioni MOCK (nessun modello, nessun audio).
In futuro si innestano i motori reali offline (openWakeWord, Vosk, Piper)
mantenendo queste interfacce.
"""

from .tts import TTS, MockTTS, make_tts
from .stt import STT, MockSTT, make_stt
from .wakeword import WakeWord, MockWakeWord, make_wakeword

__all__ = [
    "TTS", "MockTTS", "make_tts",
    "STT", "MockSTT", "make_stt",
    "WakeWord", "MockWakeWord", "make_wakeword",
]
