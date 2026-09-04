"""Rilevamento della connettivita' Internet (WAN).

Nota: che un dispositivo sia collegato all'hotspot del cockpit non
implica che il Raspberry abbia Internet a monte. Qui verifichiamo una
vera raggiungibilita' verso l'esterno, non la semplice presenza di rete.
"""

import socket


def has_internet(
    host: str = "1.1.1.1",
    port: int = 53,
    timeout: float = 1.5,
) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
