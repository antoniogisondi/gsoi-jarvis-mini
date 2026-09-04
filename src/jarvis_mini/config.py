"""Configurazione di Jarvis Mini.

Valori di default pensati per lo sviluppo locale; sovrascrivibili da
variabili d'ambiente cosi' che, una volta dentro l'OS, si possano
regolare senza modificare il codice.
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    # Endpoint del server GSOI (gsoi-jarvis) per le richieste complesse.
    server_url: str = "http://localhost:8080"
    server_health_path: str = "/health"

    # Controllo connettivita' Internet (socket verso un DNS pubblico).
    net_check_host: str = "1.1.1.1"
    net_check_port: int = 53
    net_timeout: float = 1.5

    # Timeout per il controllo di raggiungibilita' del server.
    server_timeout: float = 1.5

    # Forza la modalita' offline (utile per test e diagnostica).
    force_offline: bool = False

    @property
    def health_url(self) -> str:
        return self.server_url.rstrip("/") + self.server_health_path

    @classmethod
    def from_env(cls) -> "Config":
        base = cls()
        return cls(
            server_url=os.environ.get("GSOI_SERVER_URL", base.server_url),
            server_health_path=os.environ.get(
                "GSOI_SERVER_HEALTH_PATH", base.server_health_path
            ),
            force_offline=os.environ.get("JARVIS_FORCE_OFFLINE", "0") == "1",
        )
