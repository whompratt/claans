from datetime import datetime
from enum import Enum

import mongoengine

from utils.claans import Claans
from utils.dice import Dice


class RecordType(Enum):
    """Enum denoting the type of record"""

    QUEST = "quest"
    ACTIVITY = "activity"


class Record(mongoengine.Document):
    """
    Defines a record for a quest or activity, for submission of the record into the mongo database.

    Note that this class is used for both `submit_task` and `update_score`.
    `score` and `timestamp` are generated in `__post_init__`.
    `score` requires `dice` be already defined, which itself is an instance of `Dice`, using its `roll` function.
    `timestamp` is generated using the `datetime` library, which works natively with pymongo.

    Attributes:
        user: name of the user submitting the quest or activity.
        claan: instance of enum `Claans`, defining which claan this user is in.
        type: instance of enum `RecordType`, defining whether this is a quest or activity.
        dice: instance of enum `Dice`, which defines the number of sides of the score die to roll.
    """

    user = mongoengine.StringField(required=True)
    claan = mongoengine.EnumField(Claans, required=True)
    type = mongoengine.EnumField(RecordType, required=True)
    dice = mongoengine.EnumField(Dice, required=True)
    score = mongoengine.IntField()
    timestamp = mongoengine.DateTimeField(default=datetime.now)

    @classmethod
    def post_init(cls, sender, document, **kwargs):
        document.score = document.score or document.dice.roll()


mongoengine.signals.post_init.connect(Record.post_init, sender=Record)
