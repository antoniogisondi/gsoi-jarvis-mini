"""Test della logica di routing (cervello a bordo prima, server opzionale)."""

import unittest

from jarvis_mini.ai.base import LocalAI
from jarvis_mini.ai.mock import MockLocalAI
from jarvis_mini.config import Config
from jarvis_mini.intents.engine import IntentEngine
from jarvis_mini.intents.models import Result, Source
from jarvis_mini.remote.client import RemoteClient
from jarvis_mini.router.router import Router
from jarvis_mini.tools.registry import build_default_registry


class _FakeMode:
    """ModeManager fittizio: forza la disponibilita' del server."""

    def __init__(self, server_available: bool):
        self._server_available = server_available

    def is_server_available(self) -> bool:
        return self._server_available


class _AnsweringAI(LocalAI):
    """Cervello locale che risponde sempre (modello attivo a bordo)."""

    def ask(self, text: str) -> Result:
        return Result(
            text="risposta locale",
            success=True,
            source=Source.LOCAL_AI,
            data={"query": text, "backend": "local"},
        )


def _build_router(server_available: bool, local_ai: LocalAI = None) -> Router:
    config = Config()
    return Router(
        engine=IntentEngine(),
        registry=build_default_registry(),
        mode_manager=_FakeMode(server_available),
        remote_client=RemoteClient(config),
        local_ai=local_ai or MockLocalAI(),
    )


class TestRouter(unittest.TestCase):
    def test_comando_semplice_resta_locale_anche_online(self):
        router = _build_router(server_available=True)
        result = router.handle("Alza il volume")
        self.assertEqual(result.source, Source.LOCAL_TOOL)
        self.assertTrue(result.success)

    def test_cervello_locale_risponde_senza_usare_il_server(self):
        # Modello a bordo attivo: la richiesta NON deve uscire dalla macchina,
        # anche se il server e' raggiungibile (niente round-trip di rete).
        router = _build_router(server_available=True, local_ai=_AnsweringAI())
        result = router.handle("Spiegami se ci sono anomalie nei dati OBD")
        self.assertEqual(result.source, Source.LOCAL_AI)
        self.assertTrue(result.success)

    def test_modello_assente_online_ripiega_sul_server(self):
        # Nessun modello a bordo (mock -> success=False): fallback al server.
        router = _build_router(server_available=True)
        result = router.handle("Spiegami se ci sono anomalie nei dati OBD")
        self.assertEqual(result.source, Source.REMOTE)

    def test_modello_assente_offline_resta_locale(self):
        # Nessun modello e nessun server: si restituisce l'esito locale.
        router = _build_router(server_available=False)
        result = router.handle("Spiegami se ci sono anomalie nei dati OBD")
        self.assertEqual(result.source, Source.LOCAL_AI)


if __name__ == "__main__":
    unittest.main()
