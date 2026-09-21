"""Test della VoiceSession: il cuore conversazionale dell'assistente vocale.

Verifica il percorso unico `ask()` (usato sia dal microfono sia da POST /ask):
stato del dialogo, storia, robustezza agli errori e vista per /state.
"""

import unittest

from jarvis_mini.intents.models import Result, Source
from jarvis_mini.voice.session import (
    VoiceSession, STATE_IDLE, STATE_SPEAKING, make_ask_handler,
)


class _FakeAgent:
    """Agente finto: registra cosa viene pronunciato e risponde in modo fisso."""

    def __init__(self, reply="ok", boom=False):
        self.reply = reply
        self.boom = boom
        self.spoken = []

    def handle(self, text: str) -> Result:
        if self.boom:
            raise RuntimeError("cervello ko")
        return Result(text=self.reply, success=True, source=Source.LOCAL_AI)

    def say(self, text: str) -> None:
        self.spoken.append(text)


class TestVoiceSession(unittest.TestCase):
    def test_ask_registra_dialogo_e_pronuncia(self):
        agent = _FakeAgent(reply="Fatto.")
        s = VoiceSession(agent)
        r = s.ask("apri la navigazione")

        self.assertEqual(r.text, "Fatto.")
        self.assertEqual(agent.spoken, ["Fatto."])  # ha parlato la risposta

        d = s.to_dict()
        self.assertEqual(d["state"], STATE_IDLE)   # torna a riposo a fine turno
        self.assertEqual(d["you"], "apri la navigazione")
        self.assertEqual(d["reply"], "Fatto.")
        self.assertEqual([h["role"] for h in d["history"]], ["you", "jarvis"])

    def test_testo_vuoto_ignorato(self):
        agent = _FakeAgent()
        s = VoiceSession(agent)
        r = s.ask("   ")
        self.assertFalse(r.success)
        self.assertEqual(agent.spoken, [])          # niente da pronunciare
        self.assertEqual(s.to_dict()["history"], [])

    def test_errore_cervello_non_propaga(self):
        # Se il cervello solleva, l'assistente non deve cadere: risposta di
        # cortesia, comunque pubblicata nello stato.
        agent = _FakeAgent(boom=True)
        s = VoiceSession(agent)
        r = s.ask("qualcosa di complesso")
        self.assertFalse(r.success)
        self.assertTrue(r.text)                     # messaggio di scusa non vuoto
        self.assertEqual(s.to_dict()["state"], STATE_IDLE)

    def test_no_speak_non_pronuncia(self):
        agent = _FakeAgent(reply="silenzio")
        s = VoiceSession(agent)
        s.ask("dimmi", speak=False)
        self.assertEqual(agent.spoken, [])

    def test_storia_limitata(self):
        agent = _FakeAgent(reply="r")
        s = VoiceSession(agent, max_history=4)
        for i in range(10):
            s.ask(f"q{i}")
        self.assertLessEqual(len(s.to_dict()["history"]), 4)

    def test_ask_handler_factory(self):
        agent = _FakeAgent(reply="pronto")
        handler = make_ask_handler(VoiceSession(agent))
        self.assertEqual(handler("ciao").text, "pronto")


if __name__ == "__main__":
    unittest.main()
