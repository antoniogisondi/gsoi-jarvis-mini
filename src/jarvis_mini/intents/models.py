"""Modelli dati condivisi: intenti, match e risultati."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class Intent(str, Enum):
    """Intenti locali riconosciuti da Jarvis Mini.

    UNKNOWN indica che nessun intent locale corrisponde: la richiesta e'
    quindi gestita dal cervello locale (LLM a bordo).
    """

    MEDIA_VOLUME_UP = "MEDIA_VOLUME_UP"
    MEDIA_VOLUME_DOWN = "MEDIA_VOLUME_DOWN"
    MEDIA_PAUSE = "MEDIA_PAUSE"
    MEDIA_PLAY = "MEDIA_PLAY"
    NAV_OPEN = "NAV_OPEN"
    NAV_HOME = "NAV_HOME"
    VEHICLE_ENGINE_TEMP = "VEHICLE_ENGINE_TEMP"
    VEHICLE_RPM = "VEHICLE_RPM"
    VEHICLE_BATTERY = "VEHICLE_BATTERY"
    BLUETOOTH_OPEN = "BLUETOOTH_OPEN"
    UNKNOWN = "UNKNOWN"


class Source(str, Enum):
    """Da dove proviene la risposta a una richiesta."""

    LOCAL_TOOL = "local_tool"   # eseguita da un tool locale (deterministico)
    LOCAL_AI = "local_ai"       # gestita dal cervello locale (LLM a bordo)


@dataclass
class IntentMatch:
    intent: Intent
    confidence: float
    text: str
    slots: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    text: str
    success: bool = True
    source: Source = Source.LOCAL_TOOL
    data: Dict[str, Any] = field(default_factory=dict)
