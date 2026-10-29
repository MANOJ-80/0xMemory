"""Deterministic task and query analysis for memory and code retrieval."""

import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone

from oxmemory.core.models import MemoryType


@dataclass(frozen=True)
class QueryPlan:
    intent: str
    temporal: str
    historical: bool
    symbols: list[str]
    file_paths: list[str]
    technologies: list[str]
    preferred_memory_types: list[str]
    required_slots: list[str]
    as_of: str | None

    def to_dict(self) -> dict:
        return asdict(self)


_DATE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
_MONTH_NAMES = r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
_MONTH_DAY_YEAR = re.compile(
    rf"\b({_MONTH_NAMES})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?[,]?\s+(20\d{{2}})\b", re.I
)
_DAY_MONTH_YEAR = re.compile(
    rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_NAMES})\.?[,]?\s+(20\d{{2}})\b", re.I
)
_PATH = re.compile(r"(?<![\w.-])([\w.-]+(?:/[\w.-]+)+\.(?:py|js|jsx|ts|tsx|go|rs|java|cs|cpp|h))\b")
_SYMBOL = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]{2,})\s*\([^()]*\)|\b([A-Za-z_][A-Za-z0-9_]*[A-Z][A-Za-z0-9_]*)\b")
_TECH = {
    "postgresql", "postgres", "sqlite", "mysql", "redis", "mongodb", "chromadb",
    "fastapi", "django", "flask", "react", "typescript", "python", "docker",
}


def analyze_query(query: str) -> QueryPlan:
    """Infer retrieval intent and exact entities without an LLM call."""
    text = query.strip()
    lower = text.casefold()
    words = set(re.findall(r"[a-z0-9_]+", lower))
    historical = bool(words & {"previously", "historically", "history", "before", "earlier", "tried", "replaced"})
    historical = historical or bool(re.search(r"\bused\s+to\b", lower))
    current = bool(words & {"currently", "current", "now", "today", "implemented", "configured"})
    if historical:
        intent, temporal = "historical_decision", "historical"
        preferred = [MemoryType.DECISION.value, MemoryType.LEARNING.value]
    elif words & {"approved", "approve", "approval", "decided", "decision"}:
        intent, temporal = "approval_status", "current"
        preferred = [MemoryType.DECISION.value]
    elif re.search(r"\bwhy\b|\brationale\b|\breason\b", lower):
        intent, temporal = "architectural_explanation", "current"
        preferred = [MemoryType.DECISION.value, MemoryType.LEARNING.value]
    elif current:
        intent, temporal = "current_implementation", "current"
        preferred = [MemoryType.FACT.value, MemoryType.ENVIRONMENT.value, MemoryType.DECISION.value]
    elif re.search(r"\b(where|defined|definition|symbol|function|class)\b", lower) or "(" in text:
        intent, temporal = "symbol_lookup", "current"
        preferred = [MemoryType.FACT.value, MemoryType.LEARNING.value]
    else:
        intent, temporal = "general", "unspecified"
        preferred = []
    date_match = _DATE.search(lower)
    as_of = date_match.group(1) if date_match else None
    if not as_of:
        natural_match = _MONTH_DAY_YEAR.search(text) or _DAY_MONTH_YEAR.search(text)
        if natural_match:
            try:
                parsed = datetime.strptime(natural_match.group(0).replace(",", "").replace(".", ""),
                                           "%B %d %Y" if natural_match.re is _MONTH_DAY_YEAR
                                           else "%d %B %Y")
            except ValueError:
                # Abbreviated month names use the corresponding abbreviated format.
                try:
                    parsed = datetime.strptime(
                        natural_match.group(0).replace(",", "").replace(".", ""),
                        "%b %d %Y" if natural_match.re is _MONTH_DAY_YEAR else "%d %b %Y",
                    )
                except ValueError:
                    parsed = None
            as_of = parsed.date().isoformat() if parsed else None
    if as_of:
        try:
            date.fromisoformat(as_of)
        except ValueError:
            as_of = None
        else:
            historical, temporal, intent = True, "as_of", "historical_decision"
    symbols = list(dict.fromkeys(
        symbol for match in _SYMBOL.finditer(text)
        if (symbol := (match.group(1) or match.group(2))).casefold() not in _TECH
    ))
    paths = list(dict.fromkeys(_PATH.findall(text.replace("\\", "/"))))
    technologies = sorted(words & _TECH)
    from oxmemory.storage.retrieval import requested_slots

    return QueryPlan(
        intent=intent,
        temporal=temporal,
        historical=historical,
        symbols=symbols,
        file_paths=paths,
        technologies=technologies,
        preferred_memory_types=preferred,
        required_slots=sorted(requested_slots(query)),
        as_of=as_of,
    )


def claim_valid_at(memory, when: date | None = None) -> bool:
    """Return whether explicit claim validity bounds include the requested date."""
    at = when or datetime.now(timezone.utc).date()

    def utc_date(value: datetime) -> date:
        normalized = (value.replace(tzinfo=timezone.utc) if value.tzinfo is None
                      else value.astimezone(timezone.utc))
        return normalized.date()

    if memory.valid_from and utc_date(memory.valid_from) > at:
        return False
    # Claim intervals are half-open: [valid_from, valid_to). A replacement
    # that starts at the old claim's valid_to is current on that boundary.
    if memory.valid_to and utc_date(memory.valid_to) <= at:
        return False
    return True


def claim_intervals_overlap(left, right) -> bool:
    """Whether two half-open claim-validity intervals overlap; missing bounds are open."""
    def normalize(value):
        if value is None:
            return None
        return (value.replace(tzinfo=timezone.utc) if value.tzinfo is None
                else value.astimezone(timezone.utc))

    left_start, left_end = normalize(left.valid_from), normalize(left.valid_to)
    right_start, right_end = normalize(right.valid_from), normalize(right.valid_to)
    return not ((left_end is not None and right_start is not None and left_end <= right_start)
                or (right_end is not None and left_start is not None and right_end <= left_start))
