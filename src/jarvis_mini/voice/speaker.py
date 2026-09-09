"""Riconoscimento del parlante (biometria vocale) — 'sei tu?'.

Distinto dall'STT: qui non contano le parole, ma *chi* parla. Funziona per
confronto di embedding: in enrollment si registra il profilo vocale
dell'utente; a runtime si confronta la voce corrente con i profili salvati.

  * MockSpeakerID        — finto (default): 'riconosce' il profilo registrato.
  * ResemblyzerSpeakerID — reale offline (embedding + similarita' coseno).

Tutto on-device: i profili restano in locale, la voce non lascia l'auto.
Attivare il reale con: JARVIS_SPEAKER=resemblyzer  (richiede `resemblyzer`).
"""

import json
import os
from typing import List, Optional

DEFAULT_DB = os.path.expanduser("~/.gsoi/speakers.json")


class SpeakerID:
    def enroll(self, name: str, wav_paths: List[str]) -> None:
        raise NotImplementedError

    def identify(self, wav_path: str) -> Optional[str]:
        raise NotImplementedError


def _load_db(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_db(path: str, db: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f)


class MockSpeakerID(SpeakerID):
    """Finto: memorizza i nomi; 'riconosce' l'ultimo profilo registrato."""

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path

    def enroll(self, name: str, wav_paths: List[str]) -> None:
        db = _load_db(self.db_path)
        db[name] = {"mock": True}
        _save_db(self.db_path, db)
        print(f"[SpeakerID:mock] profilo '{name}' registrato.")

    def identify(self, wav_path: str = "") -> Optional[str]:
        db = _load_db(self.db_path)
        return next(reversed(db), None) if db else None


class ResemblyzerSpeakerID(SpeakerID):
    """Reale: embedding vocale + similarita' coseno."""

    def __init__(self, db_path: str = DEFAULT_DB, threshold: float = 0.75):
        self.db_path = db_path
        self.threshold = threshold
        self._encoder = None

    def _enc(self):
        if self._encoder is None:
            from resemblyzer import VoiceEncoder
            self._encoder = VoiceEncoder()
        return self._encoder

    def _embed(self, wav_path: str):
        from resemblyzer import preprocess_wav
        import numpy as np
        wav = preprocess_wav(wav_path)
        return self._enc().embed_utterance(wav), np

    def enroll(self, name: str, wav_paths: List[str]) -> None:
        import numpy as np
        embs = [self._embed(w)[0] for w in wav_paths]
        mean = np.mean(embs, axis=0)
        db = _load_db(self.db_path)
        db[name] = {"embedding": mean.tolist()}
        _save_db(self.db_path, db)
        print(f"[SpeakerID] profilo '{name}' registrato ({len(wav_paths)} campioni).")

    def identify(self, wav_path: str) -> Optional[str]:
        try:
            emb, np = self._embed(wav_path)
            db = _load_db(self.db_path)
            best, best_score = None, 0.0
            for name, rec in db.items():
                ref = rec.get("embedding")
                if not ref:
                    continue
                ref = np.array(ref)
                score = float(np.dot(emb, ref) /
                              (np.linalg.norm(emb) * np.linalg.norm(ref)))
                if score > best_score:
                    best, best_score = name, score
            return best if best_score >= self.threshold else None
        except Exception as exc:
            print(f"[SpeakerID:errore] {exc}")
            return None


def make_speaker() -> SpeakerID:
    db = os.environ.get("JARVIS_SPEAKER_DB", DEFAULT_DB)
    if os.environ.get("JARVIS_SPEAKER") == "resemblyzer":
        return ResemblyzerSpeakerID(db)
    return MockSpeakerID(db)
