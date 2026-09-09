"""Motore che valuta le regole proattive sulla telemetria corrente."""

from typing import List

from .rules import DEFAULT_RULES, Suggestion


class ProactiveEngine:
    def __init__(self, rules=None):
        self.rules = rules if rules is not None else DEFAULT_RULES

    def evaluate(self, telemetry: dict) -> List[Suggestion]:
        out = []
        for rule in self.rules:
            try:
                s = rule(telemetry)
            except Exception:
                s = None
            if s is not None:
                out.append(s)
        return out
