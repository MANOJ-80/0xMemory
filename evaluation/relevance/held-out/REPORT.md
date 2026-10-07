# Relevance experiment: held_out

Frozen threshold: **0.25**. Model: all-MiniLM-L6-v2.

| Variant | Answer recall | False abstention | No-answer false positive |
| --- | ---: | ---: | ---: |
| ungated | 100.0% | 0.0% | 100.0% |
| gated | 100.0% | 0.0% | 100.0% |

Answerable cases: 8; no-answer cases: 8.

## Failures

- test-owner: Who is the security incident commander? Returned ['m0', 'm1']; expected relevant IDs [].
- test-budget: What budget is allocated to cloud storage? Returned ['m0', 'm1']; expected relevant IDs [].
- test-approval: Who approved the rate limit settings? Returned ['m0']; expected relevant IDs [].
- test-law: Which jurisdiction governs customer contracts? Returned ['m0', 'm1']; expected relevant IDs [].
- test-rpo: What recovery point objective did the business agree to? Returned ['m1']; expected relevant IDs [].
- test-vendor: When does our cloud vendor contract expire? Returned ['m0']; expected relevant IDs [].
- test-contact: What is the emergency support phone number? Returned ['m0', 'm1']; expected relevant IDs [].
- test-why: Why did the team choose this message broker? Returned ['m0', 'm1']; expected relevant IDs [].

## Limits

- Assistant-authored synthetic data; independent label review pending
- No-answer labels include missing rationale and ownership questions
- Cosine similarity measures relatedness, not answer entailment
- No production coding-success or general accuracy claim