"""Telemetria del veicolo (mock).

Fornisce uno snapshot dei dati veicolo per il cockpit. Volutamente
generico (EV + ICE): include sia giri/temperatura (termico) sia
carica/autonomia (elettrico). In futuro sara' alimentato da OBD reale
(sola lettura).
"""

import random


def snapshot(mode: str = "offline") -> dict:
    return {
        "mode": mode,
        "vehicle": {
            "speed": random.randint(0, 90),
            "rpm": random.randint(800, 3000),
            "engine_temp": random.randint(86, 94),
            "battery_v": round(random.uniform(12.2, 14.4), 1),
            "charge_pct": 84,
            "range_km": 412,
        },
        "media": {
            "title": "Ostinato",
            "artist": "Marta Bellini Trio",
        },
        "connection": {
            "online": mode == "connected",
        },
    }
