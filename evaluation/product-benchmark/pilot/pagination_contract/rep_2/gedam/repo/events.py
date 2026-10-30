"""Return a page of events and a cursor for the next page, if any."""

import base64
import json


DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _encode_cursor(event_id):
    payload = json.dumps(event_id, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(cursor):
    if not isinstance(cursor, str) or not cursor:
        raise ValueError("cursor must be a non-empty URL-safe base64 string")
    try:
        encoded = cursor.encode("ascii")
        payload = base64.urlsafe_b64decode(encoded + b"=" * (-len(encoded) % 4))
        return json.loads(payload.decode("utf-8"))
    except (UnicodeEncodeError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("invalid cursor") from exc


def list_events(events, limit=None, cursor=None):
    """List events in input order, continuing after the ID encoded in cursor.

    Events are mappings with an ``id`` field. The cursor identifies the last
    event returned on the previous page, so that event itself is never repeated.
    """
    if limit is None:
        page_size = DEFAULT_LIMIT
    else:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        page_size = min(limit, MAX_LIMIT)

    event_list = list(events)
    start = 0
    if cursor is not None:
        last_id = _decode_cursor(cursor)
        for index, event in enumerate(event_list):
            if event["id"] == last_id:
                start = index + 1
                break
        else:
            raise ValueError("cursor does not identify an event in this collection")

    page = event_list[start : start + page_size]
    next_cursor = None
    if start + len(page) < len(event_list):
        next_cursor = _encode_cursor(page[-1]["id"])
    return {"items": page, "next_cursor": next_cursor}
