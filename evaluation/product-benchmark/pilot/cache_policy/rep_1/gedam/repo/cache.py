from collections import OrderedDict


class ResultCache:
    """A bounded least-recently-used cache for worker results."""

    MAX_ENTRIES = 64

    def __init__(self):
        self._entries = OrderedDict()

    def get(self, key):
        try:
            value = self._entries.pop(key)
        except KeyError:
            return None
        self._entries[key] = value
        return value

    def put(self, key, value):
        # Reinsert existing keys at the end so updates refresh their recency.
        self._entries.pop(key, None)
        self._entries[key] = value
        if len(self._entries) > self.MAX_ENTRIES:
            self._entries.popitem(last=False)
