"""Controllo di raggiungibilita' del server GSOI (gsoi-jarvis).

Usa solo la libreria standard: nessuna dipendenza esterna, coerente con
l'obiettivo offline-first e a basso consumo su Raspberry Pi 5.
"""

import urllib.error
import urllib.request


def is_server_reachable(health_url: str, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(health_url, timeout=timeout) as response:
            return 200 <= response.status < 500
    except (urllib.error.URLError, OSError, ValueError):
        return False
