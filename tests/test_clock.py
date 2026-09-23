"""Test dell'ora/data locale: l'auto risponde senza scomodare l'LLM."""

import unittest
from datetime import datetime

from jarvis_mini.intents.engine import IntentEngine
from jarvis_mini.intents.models import Intent, Source
from jarvis_mini.tools.local_tools import ClockTool
from jarvis_mini.router.router import Router
from jarvis_mini.tools.registry import build_default_registry
from jarvis_mini.ai.mock import MockLocalAI


class TestClockIntent(unittest.TestCase):
    def setUp(self):
        self.engine = IntentEngine()

    def test_ora_riconosciuta(self):
        for q in ["Che ore sono?", "che ora è", "dimmi l'ora", "che orario è?"]:
            self.assertEqual(self.engine.recognize(q).intent, Intent.TIME_NOW, q)

    def test_data_riconosciuta(self):
        for q in ["Che giorno è oggi?", "che data è", "in che giorno siamo oggi"]:
            self.assertEqual(self.engine.recognize(q).intent, Intent.DATE_TODAY, q)

    def test_ora_non_confonde_apri_ora(self):
        # "apri ora la mappa" NON deve diventare una richiesta d'orario.
        self.assertNotEqual(self.engine.recognize("apri ora la mappa").intent,
                            Intent.TIME_NOW)


class TestClockTool(unittest.TestCase):
    def _tool(self):
        fixed = datetime(2026, 9, 23, 9, 5)  # mercoledì
        return ClockTool(now=lambda: fixed)

    def test_ora_formattata(self):
        r = self._tool().execute(
            IntentEngine().recognize("che ore sono?"))
        self.assertIn("09:05", r.text)
        self.assertTrue(r.success)

    def test_data_in_italiano(self):
        from jarvis_mini.intents.models import IntentMatch
        r = self._tool().execute(IntentMatch(Intent.DATE_TODAY, 1.0, ""))
        self.assertIn("mercoledì", r.text)
        self.assertIn("settembre", r.text)
        self.assertIn("2026", r.text)


class TestClockRouting(unittest.TestCase):
    def test_ora_resta_locale_niente_llm(self):
        router = Router(IntentEngine(), build_default_registry(), MockLocalAI())
        r = router.handle("che ore sono?")
        self.assertEqual(r.source, Source.LOCAL_TOOL)
        self.assertTrue(r.success)


if __name__ == "__main__":
    unittest.main()
