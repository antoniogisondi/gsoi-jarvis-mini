"""Test del client del modello locale (OpenAI-compatible su localhost).

Nessuna rete reale: si sostituisce urllib.request.urlopen con uno stub.
"""

import io
import json
import unittest
import urllib.error
from unittest import mock

from jarvis_mini.ai.model_client import LocalModelClient
from jarvis_mini.config import Config


def _fake_response(payload: dict):
    """Simula il context manager restituito da urlopen."""
    raw = json.dumps(payload).encode("utf-8")
    resp = io.BytesIO(raw)
    resp.__enter__ = lambda s: s
    resp.__exit__ = lambda s, *a: False
    return resp


class TestLocalModelClient(unittest.TestCase):
    def setUp(self):
        self.client = LocalModelClient(Config())

    def test_risposta_valida(self):
        payload = {"choices": [{"message": {"content": "Ciao, sono GSOI."}}]}
        with mock.patch("urllib.request.urlopen", return_value=_fake_response(payload)):
            result = self.client.ask("chi sei?")
        self.assertTrue(result.success)
        self.assertEqual(result.text, "Ciao, sono GSOI.")
        self.assertEqual(result.data["backend"], "local")

    def test_blocco_think_rimosso(self):
        payload = {
            "choices": [
                {"message": {"content": "<think>ragiono...</think>Risposta breve."}}
            ]
        }
        with mock.patch("urllib.request.urlopen", return_value=_fake_response(payload)):
            result = self.client.ask("domanda")
        self.assertTrue(result.success)
        self.assertEqual(result.text, "Risposta breve.")

    def test_modello_irraggiungibile_fallisce_con_grazia(self):
        with mock.patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            result = self.client.ask("domanda")
        self.assertFalse(result.success)
        self.assertIn("error", result.data)


if __name__ == "__main__":
    unittest.main()
