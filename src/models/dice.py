import random
from enum import Enum


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
