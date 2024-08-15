from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Claan(Enum):
    EARTH_STRIDERS = "Earth Striders"
    FIRE_DANCERS = "Fire Dancers"
    THUNDER_WALKERS = "Thunder Walkers"
    WAVE_RIDERS = "Wave Riders"

    def get_icon(self):
        match self.name:
            case "EARTH_STRIDERS":
                return ":rock:"
            case "FIRE_DANCERS":
                return ":fire:"
            case "THUNDER_WALKERS":
                return ":lightning_cloud:"
            case "WAVE_RIDERS":
                return ":ocean:"
