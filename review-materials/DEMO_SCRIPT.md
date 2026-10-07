# Ten-minute review demonstration

Use a fresh Dodo copy prepared with START_HERE. Keep the completed original run as
backup evidence; do not reset its history. Test your editor login and cached model
before the presentation. Keep the relevance gate disabled for the lifecycle demo.

| Time | Action | Evidence to display |
| --- | --- | --- |
| 0:00–1:00 | Explain lost context and outdated decisions | Problem and architecture slides |
| 1:00–2:00 | Show separate app and memory project | MCP status, JSON app, five starter tests |
| 2:00–3:00 | Save JSON decision and rationale | Actual remember response and ID |
| 3:00–4:00 | Start fresh chat and recall | Same ID and rationale through MCP |
| 4:00–5:30 | Show prepared/reviewed SQLite migration | Git diff, tests, migration commit |
| 5:30–6:30 | Observe migration | Old memory marked stale; normal recall excludes it |
| 6:30–7:30 | Review and supersede | Old/new entries with evidence and links |
| 7:30–8:00 | Start fresh chat again | Current SQLite decision and new ID |
| 8:00–9:00 | Explain controlled lifecycle results | 12/12 to 0/12 outdated retrieval, with recall tradeoff |
| 9:00–10:00 | Explain relevance failure and remaining work | No-answer gate failed on new reserved cases |

For a short review, prepare the code migration before the talk but do not pretend
the agent implemented it live. Keep explicit commit observation and supersession
visible. Agent generation and model downloads should not consume the demonstration.

## Likely viva questions

**What is your contribution beyond storing chat history?**
We attach decisions to code evidence, explicitly detect affected evidence after a
commit, require review, preserve supersession history, and filter retrieval by state.

**Does a file change prove a memory is false?**
No. It becomes stale pending review. Verification restores a still-valid claim;
supersession records a changed decision.

**Does this work automatically after every edit?**
No. Commit observation and review are explicit. There is no background watcher.

**Why did recall fall to 75%?**
Five still-true memories were withheld while their changed evidence awaited review.
They were retrieved after verification. The metric exposes that cost.

**Did you solve hallucinations?**
No. We measured retrieved context, not LLM answers. The threshold experiment did
not solve unanswered questions with related vocabulary.

**Why not increase the cosine threshold until it works?**
Higher thresholds hid useful development answers. We froze a development-selected
policy before testing. Tuning it on the inspected test cases would invalidate the
claim that they are reserved evaluation data.

**Is 0.25 a confidence probability?**
No. It is an experimental cosine-similarity cutoff for this model and dataset.

**Why Markdown and ChromaDB?**
Markdown is inspectable authoritative storage; the vector index supports semantic
search and can be rebuilt. This prototype uses one writer process per project.

**What is independently validated?**
The developer reported the Copilot demo and original full Windows test run. Our
automated experiments are repeatable synthetic checks. The friend's independent
report and additional editor UI demonstrations are separate, still-pending evidence.

**What comes next?**
Human-labelled real-repository cases, answerability-aware retrieval, review-quality
evaluation, and matched-model coding tasks. These are future work, not claimed results.
