"""Small deterministic checks for obvious credential material before persistence."""

import re

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"]?[^\s'\"]{12,}"),
)


def contains_obvious_secret(*values: object) -> bool:
    """Check user-visible memory claim fields for common credential patterns."""
    return any(pattern.search(str(value)) for value in values if value is not None
               for pattern in _SECRET_PATTERNS)
