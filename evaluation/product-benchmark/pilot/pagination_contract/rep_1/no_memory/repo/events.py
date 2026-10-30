def list_events(events, limit=None, cursor=None):
    """Return a page of events using an integer offset cursor.

    ``cursor`` is the zero-based index at which to start.  When a limited
    page has more events after it, ``next_cursor`` is the index of the first
    event on the next page; otherwise it is ``None``.
    """
    values = list(events)
    start = 0 if cursor is None else cursor

    if not isinstance(start, int) or isinstance(start, bool) or start < 0:
        raise ValueError("cursor must be a non-negative integer")
    if limit is not None and (
        not isinstance(limit, int) or isinstance(limit, bool) or limit < 0
    ):
        raise ValueError("limit must be a non-negative integer or None")

    if limit is None:
        items = values[start:]
        next_cursor = None
    else:
        items = values[start : start + limit]
        position = start + len(items)
        next_cursor = position if position < len(values) else None

    return {"items": items, "next_cursor": next_cursor}
