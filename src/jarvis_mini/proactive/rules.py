"""Regole proattive: dalla telemetria a suggerimenti/avvisi.

Ogni regola e' una funzione telemetry(dict) -> Suggestion | None.
Deliberatamente semplice e deterministica (niente ML). GSOI deve essere
PROATTIVO: quando ha senso anticipa il bisogno e PROPONE un'azione ("Vuoi
che..."), senza eseguirla da solo. Ogni suggerimento ha un id: l'app lo
pronuncia una sola volta finche' la condizione resta attiva.

La telemetria qui e' lo snapshot di jarvis-mini (telemetry.snapshot):
    {"mode", "vehicle": {speed, rpm, engine_temp, battery_v, charge_pct,
     range_km}, "media": {...}, "connection": {online}}
"""

from dataclasses import dataclass


@dataclass
class Suggestion:
    id: str
    text: str
    severity: str = "info"  # "info" | "warn" | "critical"


def _veh(t: dict) -> dict:
    return t.get("vehicle", {}) or {}


def engine_temp_rule(t: dict):
    """Temperatura motore: avviso a 93°, allarme serio a 105°."""
    temp = _veh(t).get("engine_temp")
    if temp is None:
        return None
    if temp >= 105:
        return Suggestion(
            "engine_temp_crit",
            f"Temperatura motore critica ({temp}°). Ferma in sicurezza appena puoi.",
            "critical",
        )
    if temp >= 93:
        return Suggestion(
            "engine_temp",
            f"Temperatura motore alta ({temp}°). Tieni d'occhio e vai piano.",
            "warn",
        )
    return None


def battery_rule(t: dict):
    v = _veh(t).get("battery_v")
    if v is not None and v < 12.4:
        return Suggestion(
            "battery",
            f"Tensione batteria bassa ({v} V). Vuoi che controlli lo stato di ricarica?",
            "warn",
        )
    return None


def range_rule(t: dict):
    """Autonomia bassa: proponi subito il rifornimento."""
    km = _veh(t).get("range_km")
    if km is None:
        return None
    if km < 30:
        return Suggestion(
            "range_crit",
            f"Autonomia molto bassa ({km} km). Vuoi che ti porti subito al rifornimento piu' vicino?",
            "critical",
        )
    if km < 60:
        return Suggestion(
            "range",
            f"Autonomia in calo ({km} km). Vuoi che cerchi un rifornimento lungo il percorso?",
            "warn",
        )
    return None


def fuel_level_rule(t: dict):
    """Livello carburante/carica basso (percentuale)."""
    pct = _veh(t).get("charge_pct")
    if pct is not None and pct <= 15:
        return Suggestion(
            "fuel_low",
            f"Livello basso ({pct}%). Conviene fare rifornimento. Vuoi che cerchi dove?",
            "warn",
        )
    return None


def overrev_rule(t: dict):
    """Giri alti a lungo: suggerisci di salire di marcia per consumare meno."""
    rpm = _veh(t).get("rpm")
    speed = _veh(t).get("speed")
    # Solo in marcia (non da fermo/sgasata): giri alti con velocita' moderata.
    if rpm is not None and rpm >= 3500 and (speed is None or speed >= 20):
        return Suggestion(
            "overrev",
            "Stai tenendo giri alti: prova a salire di marcia, consumi meno.",
            "info",
        )
    return None


def speeding_rule(t: dict):
    """Velocita' elevata: promemoria gentile di sicurezza."""
    speed = _veh(t).get("speed")
    if speed is not None and speed >= 135:
        return Suggestion(
            "speeding",
            f"Stai andando a {speed} km/h: occhio ai limiti e alla distanza di sicurezza.",
            "warn",
        )
    return None


DEFAULT_RULES = [
    engine_temp_rule,
    battery_rule,
    range_rule,
    fuel_level_rule,
    overrev_rule,
    speeding_rule,
]
