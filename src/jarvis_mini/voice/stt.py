"""Riconoscimento vocale (voce -> testo)."""


class STT:
    def transcribe(self) -> str:
        raise NotImplementedError


class MockSTT(STT):
    """Mock: legge una riga da stdin, simulando il parlato trascritto.
    In futuro: Vosk (offline, italiano) dal microfono.
    """

    def transcribe(self) -> str:
        try:
            return input("(parla) > ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""


def make_stt() -> STT:
    return MockSTT()
