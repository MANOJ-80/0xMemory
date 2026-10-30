"""A process-local cache for results owned by a worker.

Each ``ResultCache`` instance keeps its own values in memory.  Values live for
the lifetime of the instance; callers can create one cache per worker to keep
workers isolated.
"""


class ResultCache:
    """Store and retrieve values by key for the lifetime of this instance."""

    def __init__(self):
        self._values = {}

    def get(self, key):
        """Return the value for *key*, or ``None`` if it is not cached."""
        return self._values.get(key)

    def put(self, key, value):
        """Store *value* under *key*. Replacing a key updates its value."""
        self._values[key] = value
