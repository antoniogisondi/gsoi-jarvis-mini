"""GSOI Jarvis Mini — Car Agent locale e offline-first per GSOI Automotive OS.

Jarvis Mini e' l'agente locale dell'automobile: gira integrato nell'OS
come servizio systemd. Il cervello e' sempre a bordo (LLM locale su
localhost): le richieste non escono dalla macchina e l'auto funziona anche
completamente offline. La rete, quando c'e', serve solo alle funzioni che
la richiedono (traffico, meteo, OTA), non a "pensare".
"""

__version__ = "0.1.0"
