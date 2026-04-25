from bson import ObjectId
from bson.errors import InvalidId

from app.application.common.exceptions import ValidationError


def parse_object_id(identifier: str, *, field_name: str = "id") -> ObjectId:
    try:
        return ObjectId(identifier)
    except (InvalidId, TypeError) as exc:
        raise ValidationError("Invalid object id") from exc


def normalize_object_id_reference(identifier):
    if identifier is None:
        return None

    if isinstance(identifier, ObjectId):
        return identifier

    if isinstance(identifier, str):
        normalized_identifier = identifier.strip()
        if not normalized_identifier:
            return None

        try:
            return ObjectId(normalized_identifier)
        except InvalidId:
            return normalized_identifier

    return identifier


def stringify_object_id(object_id: ObjectId | None) -> str | None:
    if object_id is None:
        return None
    return str(object_id)
