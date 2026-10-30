class ResultCache:
    """A process-local cache for worker results."""

    def __init__(self):
        self._values = {}

    def get(self, key):
        return self._values.get(key)

    def put(self, key, value):
        self._values[key] = value
