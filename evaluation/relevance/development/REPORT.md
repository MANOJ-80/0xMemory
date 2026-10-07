# Relevance experiment: development

Frozen threshold: **0.25**. Model: all-MiniLM-L6-v2.

| Variant | Answer recall | False abstention | No-answer false positive |
| --- | ---: | ---: | ---: |
| ungated | 100.0% | 0.0% | 100.0% |
| gated | 100.0% | 0.0% | 50.0% |

Answerable cases: 4; no-answer cases: 4.

## Failures

- dev-same-topic: Who approved the webhook retry policy? Returned ['m0', 'm1']; expected relevant IDs [].
- dev-cost: What is the monthly database hosting cost? Returned ['m0', 'm1']; expected relevant IDs [].

## Limits

- Assistant-authored synthetic data; independent label review pending
- No-answer labels include missing rationale and ownership questions
- Cosine similarity measures relatedness, not answer entailment
- No production coding-success or general accuracy claim