"""Return one page of events and a cursor for the following page."""

import base64
import binascii


_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100


def _encode_cursor(event_id):
    # Store the ID's string form so cursors remain URL-safe and independent of
    # the event's other fields.
    value = str(event_id).encode("utf-8")
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_cursor(cursor):
    if not isinstance(cursor, str) or not cursor:
        raise ValueError("cursor must be a non-empty URL-safe base64 string")
    try:
        encoded = cursor.encode("ascii")
        encoded += b"=" * (-len(encoded) % 4)
        event_id = base64.b64decode(encoded, altchars=b"-_", validate=True)
        return event_id.decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError, binascii.Error) as exc:
        raise ValueError("invalid cursor") from exc


def list_events(events, limit=None, cursor=None):
    """Return ``{"items": [...], "next_cursor": token_or_none}``.

    The cursor identifies the last event on the previous page. The event list
    is traversed in its supplied order, and that event is excluded from the
    next page.
    """
    page_size = _DEFAULT_LIMIT if limit is None else limit
    if isinstance(page_size, bool) or not isinstance(page_size, int):
        raise ValueError("limit must be an integer")
    if page_size < 1:
        raise ValueError("limit must be positive")
    page_size = min(page_size, _MAX_LIMIT)

    event_list = list(events)
    start = 0
    if cursor is not None:
        cursor_id = _decode_cursor(cursor)
        for index, event in enumerate(event_list):
            if str(event["id"]) == cursor_id:
                start = index + 1
                break
        else:
            raise ValueError("cursor does not identify an event in this list")

    items = event_list[start:start + page_size]
    has_more = start + page_size < len(event_list)
    next_cursor = _encode_cursor(items[-1]["id"]) if items and has_more else None
    return {"items": items, "next_cursor": next_cursor}
