"""Test della logica di routing."""

import unittest

from jarvis_mini.ai.local import LocalAI
from jarvis_mini.config import Config
from jarvis_mini.intents.engine import IntentEngine
from jarvis_mini.intents.models import Source
from jarvis_mini.remote.client import RemoteClient
from jarvis_mini.router.router import Router
from jarvis_mini.tools.registry import build_default_registry


class _FakeMode:
    """ModeManager fittizio: forza la disponibilita' del server."""

    def __init__(self, server_available: bool):
        self._server_available = server_available

    def is_server_available(self) -> bool:
        return self._server_available


def _build_router(server_available: bool) -> Router:
    config = Config()
    return Router(
        engine=IntentEngine(),
        registry=build_default_registry(),
        mode_manager=_FakeMode(server_available),
        remote_client=RemoteClient(config),
        local_ai=LocalAI(),
    )


class TestRouter(unittest.TestCase):
    def test_comando_semplice_resta_locale_anche_online(self):
        router = _build_router(server_available=True)
        result = router.handle("Alza il volume")
        self.assertEqual(result.source, Source.LOCAL_TOOL)
        self.assertTrue(result.success)

    def test_richiesta_complessa_online_va_al_server(self):
        router = _build_router(server_available=True)
        result = router.handle("Spiegami se ci sono anomalie nei dati OBD")
        self.assertEqual(result.source, Source.REMOTE)

    def test_richiesta_complessa_offline_usa_ai_locale(self):
        router = _build_router(server_available=False)
        result = router.handle("Spiegami se ci sono anomalie nei dati OBD")
        self.assertEqual(result.source, Source.LOCAL_AI)


if __name__ == "__main__":
    unittest.main()
