"""Test della logica di routing (cervello 100% locale, nessun server)."""

import unittest

from jarvis_mini.ai.base import LocalAI
from jarvis_mini.ai.mock import MockLocalAI
from jarvis_mini.intents.engine import IntentEngine
from jarvis_mini.intents.models import Result, Source
from jarvis_mini.router.router import Router
from jarvis_mini.tools.registry import build_default_registry


class _AnsweringAI(LocalAI):
    """Cervello locale che risponde sempre (modello attivo a bordo)."""

    def ask(self, text: str) -> Result:
        return Result(
            text="risposta locale",
            success=True,
            source=Source.LOCAL_AI,
            data={"query": text, "backend": "local"},
        )


def _build_router(local_ai: LocalAI = None) -> Router:
    return Router(
        engine=IntentEngine(),
        registry=build_default_registry(),
        local_ai=local_ai or MockLocalAI(),
    )


class TestRouter(unittest.TestCase):
    def test_comando_semplice_resta_tool_locale(self):
        router = _build_router()
        result = router.handle("Alza il volume")
        self.assertEqual(result.source, Source.LOCAL_TOOL)
        self.assertTrue(result.success)

    def test_richiesta_complessa_va_al_cervello_locale(self):
        router = _build_router(local_ai=_AnsweringAI())
        result = router.handle("Spiegami se ci sono anomalie nei dati OBD")
        self.assertEqual(result.source, Source.LOCAL_AI)
        self.assertTrue(result.success)

    def test_modello_assente_resta_locale(self):
        # Nessun modello a bordo (mock -> success=False): niente server,
        # si restituisce comunque un esito locale.
        router = _build_router()
        result = router.handle("Spiegami se ci sono anomalie nei dati OBD")
        self.assertEqual(result.source, Source.LOCAL_AI)
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
