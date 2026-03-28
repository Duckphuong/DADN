from bson import ObjectId
from bson.errors import InvalidId

from app.application.common.exceptions import ValidationError


def parse_object_id(identifier: str, *, field_name: str = "id") -> ObjectId:
    try:
        return ObjectId(identifier)
    except (InvalidId, TypeError) as exc:
        raise ValidationError("Invalid object id") from exc


def stringify_object_id(object_id: ObjectId | None) -> str | None:
    if object_id is None:
        return None
    return str(object_id)
