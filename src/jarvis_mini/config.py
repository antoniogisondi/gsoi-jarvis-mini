"""Configurazione di Jarvis Mini.

Valori di default pensati per lo sviluppo locale; sovrascrivibili da
variabili d'ambiente cosi' che, una volta dentro l'OS, si possano
regolare senza modificare il codice.
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    # Controllo connettivita' Internet (socket verso un DNS pubblico).
    # Serve solo alle funzioni online (traffico, meteo, OTA), non al cervello.
    net_check_host: str = "1.1.1.1"
    net_check_port: int = 53
    net_timeout: float = 1.5

    # Forza la modalita' offline (utile per test e diagnostica).
    force_offline: bool = False

    # --- Cervello a bordo: modello LLM locale -------------------------------
    # Il modello (Qwen3-4B-Instruct) gira come servizio separato dentro l'OS
    # ed espone un endpoint OpenAI-compatible su localhost (es. llama.cpp
    # server / Ollama / TensorRT-LLM). Jarvis Mini lo interroga senza rete:
    # nessun round-trip client-server, solo generazione locale.
    #
    #   ai_backend = "mock"  -> nessun modello (sviluppo senza hardware)
    #   ai_backend = "local" -> client OpenAI-compatible verso model_url
    ai_backend: str = "mock"
    model_url: str = "http://127.0.0.1:8091/v1"
    model_name: str = "qwen3-4b-instruct"
    model_timeout: float = 30.0
    model_temperature: float = 0.5
    model_max_tokens: int = 512

    @property
    def model_chat_url(self) -> str:
        return self.model_url.rstrip("/") + "/chat/completions"

    @classmethod
    def from_env(cls) -> "Config":
        base = cls()
        return cls(
            force_offline=os.environ.get("JARVIS_FORCE_OFFLINE", "0") == "1",
            ai_backend=os.environ.get("JARVIS_AI", base.ai_backend),
            model_url=os.environ.get("JARVIS_MODEL_URL", base.model_url),
            model_name=os.environ.get("JARVIS_MODEL_NAME", base.model_name),
            model_timeout=_env_float(
                "JARVIS_MODEL_TIMEOUT", base.model_timeout
            ),
            model_temperature=_env_float(
                "JARVIS_MODEL_TEMPERATURE", base.model_temperature
            ),
            model_max_tokens=_env_int(
                "JARVIS_MODEL_MAX_TOKENS", base.model_max_tokens
            ),
        )


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ[name])
    except (KeyError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return default
