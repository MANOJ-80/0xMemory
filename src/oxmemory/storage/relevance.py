"""Conservative candidate eligibility, separate from reciprocal-rank fusion."""

import math
import re

# Calibrated on development fixtures only; see evaluation/relevance/README.md.
DEFAULT_MIN_SIMILARITY = 0.25
STOPWORDS = set(
    "a an the is are was were be been do does did how what which who when where why "
    "can could should would we our it its of for to in on at by with and or "
    "this that these those as from have has use used using tell me about".split()
)


def cosine_similarity(left, right):
    if len(left) != len(right) or not left:
        raise ValueError("Embedding dimensions must match and be nonempty")
    norm = math.sqrt(sum(float(v) ** 2 for v in left) * sum(float(v) ** 2 for v in right))
    return (
        sum(float(a) * float(b) for a, b in zip(left, right, strict=True)) / norm if norm else 0.0
    )


def relevant(query, memory, similarity=None, threshold=DEFAULT_MIN_SIMILARITY):
    if not math.isfinite(threshold) or not -1 <= threshold <= 1:
        raise ValueError("Similarity threshold must be finite and between -1 and 1")
    if similarity is not None:
        return math.isfinite(similarity) and similarity >= threshold
    words = set(re.findall(r"\w+", query.lower())) - STOPWORDS
    text = " ".join([memory.content, *memory.tags, *memory.symbols]).lower()
    overlap = words & set(re.findall(r"\w+", text))
    # File hints influence ranking, but cannot turn unrelated text into an answer.
    return bool(words) and len(overlap) >= max(1, math.ceil(len(words) * 0.5))
