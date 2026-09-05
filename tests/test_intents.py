"""Test del motore di riconoscimento intenti."""

import unittest

from jarvis_mini.intents.engine import IntentEngine
from jarvis_mini.intents.models import Intent


class TestIntentEngine(unittest.TestCase):
    def setUp(self):
        self.engine = IntentEngine()

    def test_comandi_di_esempio(self):
        # Frasi prese dagli esempi del progetto (sezione 5).
        casi = {
            "Alza il volume": Intent.MEDIA_VOLUME_UP,
            "Abbassa il volume": Intent.MEDIA_VOLUME_DOWN,
            "Metti in pausa": Intent.MEDIA_PAUSE,
            "Apri la navigazione": Intent.NAV_OPEN,
            "Torna alla home": Intent.NAV_HOME,
            "Che temperatura ha il motore?": Intent.VEHICLE_ENGINE_TEMP,
            "Quanti giri sta facendo?": Intent.VEHICLE_RPM,
            "Qual è la tensione della batteria?": Intent.VEHICLE_BATTERY,
            "Apri Bluetooth": Intent.BLUETOOTH_OPEN,
        }
        for frase, atteso in casi.items():
            with self.subTest(frase=frase):
                self.assertEqual(self.engine.recognize(frase).intent, atteso)

    def test_sinonimi_estesi(self):
        # Modi di dire alternativi che devono comunque essere capiti.
        casi = {
            "alza l'audio": Intent.MEDIA_VOLUME_UP,
            "più forte": Intent.MEDIA_VOLUME_UP,
            "abbassa la musica": Intent.MEDIA_VOLUME_DOWN,
            "più piano": Intent.MEDIA_VOLUME_DOWN,
            "metti in pausa la musica": Intent.MEDIA_PAUSE,
            "fai partire la musica": Intent.MEDIA_PLAY,
            "apri il navigatore": Intent.NAV_OPEN,
            "portami a casa": Intent.NAV_OPEN,
            "vai alla home": Intent.NAV_HOME,
            "numero di giri": Intent.VEHICLE_RPM,
            "quanti volt ha la batteria": Intent.VEHICLE_BATTERY,
            "connetti il telefono": Intent.BLUETOOTH_OPEN,
        }
        for frase, atteso in casi.items():
            with self.subTest(frase=frase):
                self.assertEqual(self.engine.recognize(frase).intent, atteso)

    def test_richiesta_non_riconosciuta(self):
        match = self.engine.recognize(
            "Analizza i dati OBD degli ultimi trenta minuti"
        )
        self.assertEqual(match.intent, Intent.UNKNOWN)

    def test_gruppo_piu_specifico_vince(self):
        # "temperatura motore" (2 parole) e' piu' specifico di "temperatura".
        match = self.engine.recognize("temperatura del motore")
        self.assertEqual(match.intent, Intent.VEHICLE_ENGINE_TEMP)


if __name__ == "__main__":
    unittest.main()
