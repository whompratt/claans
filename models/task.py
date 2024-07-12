import mongoengine

from models.record import Dice, RecordType


class Task(mongoengine.Document):
    """
    Definition for a quest or activity.

    This class is used to standardize definitions for quests and activities, for submission into the database.
    By persisting task definitions, we can not only track _which_ tasks have been used before and _when_, but also re-use tasks automatically.
    Note that the format of the dict will _not_ match the format of the class.
    For example, the class has an attribute `dice` of type `Dice`, but the returned dict will contain the dice _name_, i.e. `D4`.

    Attributes:
        description: long description of task requirements.
        type: instance of RecordType, denoting a quest or activity.
        dice: list of instances of enum `Dice` defining the potential rewards for this task, meaning tasks can flex.
        ephemeral: bool defining whether this task can be active more than once.
        last: datetime defining fortnight when last active, to avoid rapid re-use of a single task and to also filter ephemeral tasks.
    """

    description = mongoengine.StringField(required=True)
    type = mongoengine.EnumField(RecordType, required=True)
    dice = mongoengine.ListField(mongoengine.EnumField(Dice), required=True)
    ephemeral = mongoengine.BooleanField(default=False)
    last = mongoengine.DateTimeField()
