import random
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, IntEnum

from .claans import Claans


class RecordType(IntEnum):
    """Enum denoting the type of record"""

    QUEST = 1
    ACTIVITY = 2


class Dice(Enum):
    """Enum denoting the number of sides on the score die."""

    D4 = 4
    D6 = 6
    D8 = 8
    D10 = 10
    D12 = 12

    def roll(self):
        """Randomizes actual score using randint between 1 and this die's value."""
        return random.randint(1, self.value)


@dataclass
class Record:
    """
    Defines a record for a quest or activity, for submission of the record into the mongo database.

    Note that this class is used for both `submit_quest` and `update_score`.
    `score` and `timestamp` are generated in `__post_init__`.
    `score` requires `dice` be already defined, which itself is an instance of `Dice`, using its `roll` function.
    `timestamp` is generated using the `datetime` library, which works natively with pymongo.

    Attributes:
        user: name of the user submitting the quest or activity.
        claan: instance of enum `Claans`, defining which claan this user is in.
        type: instance of enum `RecordType`, defining whether this is a quest or activity.
        dice: instance of enum `Dice`, which defines the number of sides of the score die to roll.
    """

    user: str
    claan: Claans
    type: RecordType
    dice: Dice

    def __post_init__(self):
        self.score = self.dice.roll()
        self.timestamp = datetime.now(tz=timezone.utc)

    def as_dict(self):
        """Returns this record as a formatted dict."""
        return {
            "user": self.user,
            "claan": self.claan.name,
            "type": self.type.name,
            "dice": self.dice.name,
            "score": self.score,
            "timestamp": self.timestamp,
        }
