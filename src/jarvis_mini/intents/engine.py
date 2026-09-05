"""Motore di riconoscimento intenti basato su parole chiave.

Approccio deliberatamente semplice e senza LLM: per i comandi automotive
di base (sezione "AI offline" del progetto) un match diretto per parole
chiave e' piu' veloce, deterministico e a bassissimo consumo, ideale per
il Raspberry Pi 5. L'LLM interviene solo per le richieste non riconosciute.
"""

import unicodedata
from typing import Dict, List

from .models import Intent, IntentMatch


# Per ogni intent, una lista di gruppi di parole chiave.
# Il match e' un OR fra i gruppi e un AND fra le parole di un gruppo:
# l'intent scatta se TUTTE le parole di ALMENO un gruppo sono presenti.
# NB: MEDIA_PAUSE e' elencato PRIMA di MEDIA_PLAY di proposito. A parita' di
# punteggio vince il primo trovato, cosi' "metti in pausa la musica" (che
# contiene sia "pausa" sia "musica") resta correttamente una pausa.
_PATTERNS: Dict[Intent, List[List[str]]] = {
    Intent.MEDIA_VOLUME_UP: [
        ["alza", "volume"], ["aumenta", "volume"], ["volume", "su"],
        ["alza", "audio"], ["aumenta", "audio"], ["alza", "musica"],
        ["piu", "forte"], ["piu", "alto"],
    ],
    Intent.MEDIA_VOLUME_DOWN: [
        ["abbassa", "volume"], ["diminuisci", "volume"], ["volume", "giu"],
        ["abbassa", "audio"], ["abbassa", "musica"],
        ["piu", "piano"], ["piu", "basso"], ["meno", "forte"],
    ],
    Intent.MEDIA_PAUSE: [
        ["pausa"], ["metti", "pausa"], ["ferma", "musica"],
        ["stop", "musica"], ["ferma", "audio"],
    ],
    Intent.MEDIA_PLAY: [
        ["riprendi"], ["play"], ["riproduci"], ["riparti"],
        ["metti", "musica"], ["avvia", "musica"], ["metti", "canzone"],
        ["fai", "partire"], ["fai", "suonare"],
    ],
    Intent.NAV_OPEN: [
        ["apri", "navigazione"], ["apri", "mappa"], ["apri", "mappe"],
        ["naviga"], ["navigatore"], ["mostra", "mappa"], ["portami"],
    ],
    Intent.NAV_HOME: [
        ["torna", "home"], ["vai", "home"], ["home"],
        ["schermata", "principale"], ["schermata", "home"],
        ["pagina", "principale"],
    ],
    Intent.VEHICLE_ENGINE_TEMP: [
        ["temperatura", "motore"], ["temperatura"], ["gradi", "motore"],
        ["temperatura", "acqua"],
    ],
    Intent.VEHICLE_RPM: [
        ["giri"], ["rpm"], ["regime"], ["numero", "giri"],
    ],
    Intent.VEHICLE_BATTERY: [
        ["tensione", "batteria"], ["tensione"], ["voltaggio"], ["volt"],
        ["batteria"], ["carica", "batteria"], ["stato", "batteria"],
    ],
    Intent.BLUETOOTH_OPEN: [
        ["bluetooth"], ["connetti", "telefono"], ["accoppia", "dispositivo"],
    ],
}

_PUNCTUATION = "?!.,;:\"'()"


def _normalize(text: str) -> List[str]:
    """Minuscolo, senza accenti e senza punteggiatura -> lista di parole."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    for ch in _PUNCTUATION:
        text = text.replace(ch, " ")
    return text.split()


class IntentEngine:
    def __init__(self, patterns: Dict[Intent, List[List[str]]] = None):
        self.patterns = patterns if patterns is not None else _PATTERNS

    def recognize(self, text: str) -> IntentMatch:
        words = set(_normalize(text))

        best_intent = Intent.UNKNOWN
        best_score = 0

        for intent, groups in self.patterns.items():
            for group in groups:
                if all(keyword in words for keyword in group):
                    # Un gruppo piu' specifico (piu' parole) vince.
                    if len(group) > best_score:
                        best_score = len(group)
                        best_intent = intent

        if best_intent is Intent.UNKNOWN:
            return IntentMatch(Intent.UNKNOWN, 0.0, text)

        confidence = min(1.0, 0.5 + 0.25 * best_score)
        return IntentMatch(best_intent, confidence, text)
