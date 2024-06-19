import bson
import bson.errors
from marshmallow import ValidationError, fields


class ObjectID(fields.Field):
    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        return str(value)

    def _deserialize(self, value, attr, data):
        try:
            return bson.ObjectId(value)
        except (TypeError, bson.errors.InvalidId) as e:
            raise ValidationError(e("Invalid ObjectID."))
