from dataclasses import dataclass

from marshmallow import Schema, fields, post_load

from utils.claans import Claans
from utils.object_id import ObjectID


@dataclass
class User:
    """
    Definition for a single user.

    Attributes:
        name: string denoting this user's name.
        claan: instance of enum Claans denoting this user's claan.
    """

    name: str
    claan: Claans
    _id: str = None


class UserSchema(Schema):
    _id = ObjectID(allow_none=True)
    name = fields.Str()
    claan = fields.Enum(Claans)

    @post_load
    def make_user(self, data, **kwargs):
        return User(**data)
