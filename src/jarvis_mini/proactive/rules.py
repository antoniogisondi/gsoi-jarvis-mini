"""Regole proattive: dalla telemetria a suggerimenti/avvisi.

Ogni regola e' una funzione telemetry(dict) -> Suggestion | None.
Deliberatamente semplice e deterministica (niente ML).
"""

from dataclasses import dataclass


@dataclass
class Suggestion:
    id: str
    text: str
    severity: str = "info"  # "info" | "warn"


def engine_temp_rule(t: dict):
    temp = t.get("vehicle", {}).get("engine_temp")
    if temp is not None and temp >= 93:
        return Suggestion(
            "engine_temp",
            f"Temperatura motore alta ({temp}°). Tieni d'occhio.",
            "warn",
        )
    return None


def battery_rule(t: dict):
    v = t.get("vehicle", {}).get("battery_v")
    if v is not None and v < 12.4:
        return Suggestion(
            "battery",
            f"Tensione batteria bassa ({v} V).",
            "warn",
        )
    return None


def range_rule(t: dict):
    km = t.get("vehicle", {}).get("range_km")
    if km is not None and km < 60:
        return Suggestion(
            "range",
            f"Autonomia bassa ({km} km). Vuoi che cerchi una colonnina?",
            "warn",
        )
    return None


DEFAULT_RULES = [engine_temp_rule, battery_rule, range_rule]
