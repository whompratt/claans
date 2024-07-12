import mongoengine

from utils.claans import Claans


def validate_name(name: str):
    if len(name) == 0:
        raise mongoengine.errors.ValidationError("Name required.")


class User(mongoengine.Document):
    """
    Definition for a single user.

    Attributes:
        name: string denoting this user's name.
        claan: instance of enum Claans denoting this user's claan.
    """

    name = mongoengine.StringField(required=True, validation=validate_name)
    claan = mongoengine.EnumField(Claans, required=True)

    meta = {"indexes": [{"fields": ("name", "claan"), "unique": True}]}
