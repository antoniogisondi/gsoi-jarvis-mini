"""Test del motore proattivo: GSOI anticipa e propone, ma non infastidisce."""

import unittest

from jarvis_mini.proactive.engine import ProactiveEngine


def _snap(**veh):
    return {"vehicle": veh}


class TestProactive(unittest.TestCase):
    def setUp(self):
        self.e = ProactiveEngine()

    def _ids(self, snap):
        return {s.id for s in self.e.evaluate(snap)}

    def test_tutto_tranquillo_nessun_avviso(self):
        snap = _snap(speed=90, rpm=1800, engine_temp=88,
                     battery_v=13.8, range_km=400, charge_pct=80)
        self.assertEqual(self.e.evaluate(snap), [])

    def test_temperatura_a_livelli(self):
        self.assertIn("engine_temp", self._ids(_snap(engine_temp=95)))
        self.assertIn("engine_temp_crit", self._ids(_snap(engine_temp=107)))

    def test_autonomia_e_carburante(self):
        self.assertIn("range", self._ids(_snap(range_km=50)))
        self.assertIn("range_crit", self._ids(_snap(range_km=20)))
        self.assertIn("fuel_low", self._ids(_snap(charge_pct=10)))

    def test_giri_alti_solo_in_marcia(self):
        # giri alti da fermo (sgasata) -> niente consiglio
        self.assertNotIn("overrev", self._ids(_snap(rpm=4000, speed=0)))
        # giri alti in marcia -> consiglio di cambiare marcia
        self.assertIn("overrev", self._ids(_snap(rpm=4000, speed=60)))

    def test_velocita_elevata(self):
        self.assertIn("speeding", self._ids(_snap(speed=140)))
        self.assertNotIn("speeding", self._ids(_snap(speed=100)))

    def test_proposta_di_azione_nei_testi(self):
        # Proattivo = propone un'azione ("Vuoi che...") dove sensato.
        texts = [s.text for s in self.e.evaluate(_snap(range_km=20, charge_pct=10))]
        self.assertTrue(any("Vuoi che" in t for t in texts))


if __name__ == "__main__":
    unittest.main()
