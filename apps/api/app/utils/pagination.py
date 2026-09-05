import base64
import json
import uuid
from datetime import datetime


def encode_cursor(timestamp: datetime, row_id: uuid.UUID) -> str:
    raw = json.dumps([timestamp.isoformat(), str(row_id)]).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
    timestamp_str, id_str = json.loads(raw)
    return datetime.fromisoformat(timestamp_str), uuid.UUID(id_str)
