from dataclasses import dataclass
from datetime import datetime
from typing import List, Self

from utils.record import Dice, RecordType


@dataclass
class Quest:
    """
    Definition for a quest or activity.

    This class is used to standardize definitions for quests and activities, for submission into the database.
    By persisting quest definitions, we can not only track _which_ quests have been used before and _when_, but also re-use quests automatically.
    Note that the format of the dict will _not_ match the format of the class.
    For example, the class has an attribute `dice` of type `Dice`, but the returned dict will contain the dice _name_, i.e. `D4`.

    Attributes:
        description: long description of quest requirements.
        type: instance of RecordType, denoting a quest or activity.
        dice: list of instances of enum `Dice` defining the potential rewards for this quest, meaning quests can flex.
        ephemeral: bool defining whether this quest can be active more than once.
        last: datetime defining fortnight when last active, to avoid rapid re-use of a single quest and to also filter ephemeral quests.
    """

    description: str
    type: RecordType
    dice: List[Dice]
    ephemeral: bool
    last: datetime

    def to_dict(self):
        """Returns this record as a formatted dict."""
        return {
            "description": self.description,
            "type": self.type.name,
            "dice": [die.name for die in self.dice],
            "ephemeral": self.ephemeral,
            "last": self.last,
        }

    @classmethod
    def from_dict(cls, document: dict) -> Self:
        """
        Returns an instance of this class from an input dict.

        This could have been defined in an `__init__` function, although then any object of this type would _have_ to be defined as a dict.
        This method allows the class to function as a dataclass still, with a generated `__init__`, and have means of creation through a dict input.
        Input dict must at least have keys and values for the attributes in this class.
        Extra keys will be ignored, and missing keys will raise an AttributeError.

        Inputs:
            document: dict used to generate this instance, with keys matching this class's attributes.

        Returns:
            Quest: an instance of this class.
        """
        for attr in cls.__annotations__:
            if attr not in document:
                raise AttributeError(f"Attribute {attr} missing in input dict.")

        quest = {
            key: value for key, value in document.items() if key in cls.__annotations__
        }

        return cls(**quest)
