"""Sintesi vocale (testo -> voce)."""


class TTS:
    def say(self, text: str) -> None:
        raise NotImplementedError


class MockTTS(TTS):
    """Mock: stampa cio' che direbbe. In futuro: Piper (voce italiana offline)."""

    def say(self, text: str) -> None:
        print(f"[TTS] {text}")


def make_tts() -> TTS:
    # In futuro: se disponibile Piper, restituisci PiperTTS(); altermenti mock.
    return MockTTS()
