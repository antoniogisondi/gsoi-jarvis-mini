"""Implementazioni mock dei tool locali dell'automobile.

Ogni tool restituisce un Result con un testo pronto per essere mostrato
sul cockpit o letto dal TTS. Lo stato (volume, riproduzione) e' tenuto in
memoria solo per rendere il comportamento realistico durante i test.
"""

import random

from ..intents.models import Intent, IntentMatch, Result, Source
from .base import Tool


class AudioTool(Tool):
    def __init__(self, volume: int = 50, step: int = 10):
        self.volume = volume
        self.step = step

    def execute(self, match: IntentMatch) -> Result:
        if match.intent is Intent.MEDIA_VOLUME_UP:
            self.volume = min(100, self.volume + self.step)
            return Result(f"Volume alzato al {self.volume}%.")
        if match.intent is Intent.MEDIA_VOLUME_DOWN:
            self.volume = max(0, self.volume - self.step)
            return Result(f"Volume abbassato al {self.volume}%.")
        return Result("Comando audio non gestito.", success=False)


class MediaTool(Tool):
    def __init__(self):
        self.playing = True

    def execute(self, match: IntentMatch) -> Result:
        if match.intent is Intent.MEDIA_PAUSE:
            self.playing = False
            return Result("Riproduzione in pausa.")
        if match.intent is Intent.MEDIA_PLAY:
            self.playing = True
            return Result("Riproduzione avviata.")
        return Result("Comando media non gestito.", success=False)


class NavigationTool(Tool):
    def execute(self, match: IntentMatch) -> Result:
        if match.intent is Intent.NAV_OPEN:
            return Result("Apro la navigazione.", data={"screen": "navigation"})
        if match.intent is Intent.NAV_HOME:
            return Result("Torno alla schermata principale.", data={"screen": "home"})
        return Result("Comando navigazione non gestito.", success=False)


class VehicleTool(Tool):
    """Lettura telemetria veicolo (mock, SOLA LETTURA).

    Per sicurezza (sezione "Sicurezza automotive") questo tool non invia
    mai frame CAN: espone solo dati diagnostici in lettura.
    """

    def execute(self, match: IntentMatch) -> Result:
        if match.intent is Intent.VEHICLE_ENGINE_TEMP:
            temp = random.randint(82, 95)
            return Result(
                f"La temperatura del motore e' di {temp} gradi.",
                data={"engine_temp_c": temp},
            )
        if match.intent is Intent.VEHICLE_RPM:
            rpm = random.randint(750, 3000)
            return Result(
                f"Il motore sta girando a {rpm} giri al minuto.",
                data={"rpm": rpm},
            )
        if match.intent is Intent.VEHICLE_BATTERY:
            voltage = round(random.uniform(12.2, 14.4), 1)
            return Result(
                f"La tensione della batteria e' di {voltage} volt.",
                data={"battery_v": voltage},
            )
        return Result("Dato veicolo non disponibile.", success=False)


class BluetoothTool(Tool):
    def execute(self, match: IntentMatch) -> Result:
        return Result("Apro le impostazioni Bluetooth.", data={"screen": "bluetooth"})
