"""Registro che associa ogni intent al tool locale che lo gestisce."""

from typing import Dict

from ..intents.models import Intent
from .base import Tool
from .local_tools import (
    AudioTool,
    BluetoothTool,
    MediaTool,
    NavigationTool,
    VehicleTool,
)


def build_default_registry() -> Dict[Intent, Tool]:
    """Costruisce il registro di default con i tool mock della v0.1.

    Piu' intent possono condividere la stessa istanza di tool (es. i due
    comandi di volume usano lo stesso AudioTool, cosi' lo stato si mantiene).
    """
    audio = AudioTool()
    media = MediaTool()
    navigation = NavigationTool()
    vehicle = VehicleTool()
    bluetooth = BluetoothTool()

    return {
        Intent.MEDIA_VOLUME_UP: audio,
        Intent.MEDIA_VOLUME_DOWN: audio,
        Intent.MEDIA_PAUSE: media,
        Intent.MEDIA_PLAY: media,
        Intent.NAV_OPEN: navigation,
        Intent.NAV_HOME: navigation,
        Intent.VEHICLE_ENGINE_TEMP: vehicle,
        Intent.VEHICLE_RPM: vehicle,
        Intent.VEHICLE_BATTERY: vehicle,
        Intent.BLUETOOTH_OPEN: bluetooth,
    }
