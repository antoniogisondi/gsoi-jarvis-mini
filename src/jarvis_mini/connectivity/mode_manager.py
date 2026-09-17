"""Modalita' di connettivita': OFFLINE vs CONNECTED (solo Internet).

Il cervello e' sempre locale, quindi questa modalita' NON decide dove
elaborare le richieste: indica solo se c'e' Internet, per abilitare le
funzioni che lo richiedono (traffico, meteo, OTA). Senza rete l'auto
funziona comunque, col modello a bordo.

  * OFFLINE   -> nessuna connessione Internet
  * CONNECTED -> Internet disponibile (funzioni online abilitate)

Il controllo e' iniettabile (dependency injection) per i test senza rete.
"""

from enum import Enum
from typing import Callable, Optional

from ..config import Config
from . import network


class Mode(str, Enum):
    OFFLINE = "offline"      # nessuna connessione Internet
    CONNECTED = "connected"  # Internet disponibile (funzioni online)


class ModeManager:
    def __init__(
        self,
        config: Config,
        internet_check: Optional[Callable[[], bool]] = None,
    ):
        self.config = config
        self._internet_check = internet_check or self._default_internet_check

    def _default_internet_check(self) -> bool:
        return network.has_internet(
            self.config.net_check_host,
            self.config.net_check_port,
            self.config.net_timeout,
        )

    def has_internet(self) -> bool:
        if self.config.force_offline:
            return False
        return self._internet_check()

    def current_mode(self) -> Mode:
        return Mode.CONNECTED if self.has_internet() else Mode.OFFLINE
