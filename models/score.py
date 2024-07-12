import mongoengine

from utils.claans import Claans


class Score(mongoengine.Document):
    claan = mongoengine.EnumField(Claans, required=True, unique=True)
    score = mongoengine.IntField(default=0)
