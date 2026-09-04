"""GSOI Jarvis Mini — Car Agent locale e offline-first per GSOI Automotive OS.

Jarvis Mini e' l'agente locale dell'automobile: gira sul Raspberry Pi 5
integrato nell'OS come servizio systemd e deve funzionare anche
completamente offline. Quando il server GSOI e' raggiungibile puo'
inoltrare le richieste complesse a gsoi-jarvis / gsoi-llm, ma resta
sempre attivo e non viene mai sostituito.
"""

__version__ = "0.1.0"
