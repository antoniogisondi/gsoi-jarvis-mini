"""Interfaccia comune dei tool locali."""

from abc import ABC, abstractmethod

from ..intents.models import IntentMatch, Result


class Tool(ABC):
    """Un tool esegue l'azione associata a un intent e restituisce un Result.

    Le implementazioni della v0.1 sono mock: non toccano hardware reale.
    In fasi successive verranno sostituite da implementazioni vere
    (audio ALSA/PulseAudio, lettura OBD, ecc.) mantenendo questa interfaccia.
    """

    @abstractmethod
    def execute(self, match: IntentMatch) -> Result:
        raise NotImplementedError
