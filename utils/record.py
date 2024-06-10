import random
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, IntEnum

from .claans import Claans


class RecordType(IntEnum):
    QUEST = 1
    ACTIVITY = 2


class Dice(Enum):
    D4 = 4
    D6 = 6
    D8 = 8
    D10 = 10
    D12 = 12

    def roll(self):
        return random.randint(1, self.value)


@dataclass
class Record:
    user: str
    claan: Claans
    type: RecordType
    dice: Dice

    def __post_init__(self):
        self.score = self.dice.roll()
        self.timestamp = datetime.now(tz=timezone.utc)

    def as_dict(self):
        return {
            "user": self.user,
            "claan": self.claan.name,
            "type": self.type.name,
            "dice": self.dice.name,
            "score": self.score,
            "timestamp": self.timestamp,
        }
