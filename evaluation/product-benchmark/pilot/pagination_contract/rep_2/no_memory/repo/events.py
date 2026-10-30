def list_events(events, limit=None, cursor=None):
    """Return a page of *events* using an integer offset cursor.

    ``cursor`` is the zero-based offset of the first event in the page.  The
    returned ``next_cursor`` is the offset to use for the next page, or
    ``None`` when the page reaches the end.  With no limit, all events from
    the cursor onward are returned.
    """
    start = 0 if cursor is None else cursor
    if not isinstance(start, int) or isinstance(start, bool) or start < 0:
        raise ValueError("cursor must be a non-negative integer")

    if limit is not None:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise ValueError("limit must be a non-negative integer or None")
        stop = start + limit
    else:
        stop = len(events)

    items = events[start:stop]
    next_cursor = stop if stop < len(events) else None
    return {"items": items, "next_cursor": next_cursor}
