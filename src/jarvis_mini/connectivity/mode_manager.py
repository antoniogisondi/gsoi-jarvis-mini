"""Gestore della modalita' operativa: OFFLINE vs CONNECTED.

Combina il controllo Internet e la salute del server GSOI per decidere
se le richieste complesse possono essere inoltrate al server oppure
devono restare interamente locali (fallback automatico).

I controlli sono iniettabili (dependency injection) per rendere il
comportamento facilmente testabile senza rete reale.
"""

from enum import Enum
from typing import Callable, Optional

from ..config import Config
from . import network, server_health


class Mode(str, Enum):
    OFFLINE = "offline"      # server GSOI non raggiungibile: tutto locale
    CONNECTED = "connected"  # server GSOI raggiungibile: capacita' extra


class ModeManager:
    def __init__(
        self,
        config: Config,
        internet_check: Optional[Callable[[], bool]] = None,
        server_check: Optional[Callable[[], bool]] = None,
    ):
        self.config = config
        self._internet_check = internet_check or self._default_internet_check
        self._server_check = server_check or self._default_server_check

    def _default_internet_check(self) -> bool:
        return network.has_internet(
            self.config.net_check_host,
            self.config.net_check_port,
            self.config.net_timeout,
        )

    def _default_server_check(self) -> bool:
        return server_health.is_server_reachable(
            self.config.health_url,
            self.config.server_timeout,
        )

    def has_internet(self) -> bool:
        if self.config.force_offline:
            return False
        return self._internet_check()

    def is_server_available(self) -> bool:
        if self.config.force_offline:
            return False
        if not self.has_internet():
            return False
        return self._server_check()

    def current_mode(self) -> Mode:
        return Mode.CONNECTED if self.is_server_available() else Mode.OFFLINE
