"""Rilevamento della wake word ("Hey GSOI")."""


class WakeWord:
    def wait(self) -> bool:
        """Blocca finche' non rileva la wake word; True se rilevata."""
        raise NotImplementedError


class MockWakeWord(WakeWord):
    """Mock: non ascolta davvero. In futuro: openWakeWord/Porcupine offline."""

    def wait(self) -> bool:
        return True


def make_wakeword() -> WakeWord:
    return MockWakeWord()
