# Recorded testDodoapp demonstration

Recorded on 2026-10-07. This is the original team's result record, not a substitute
for the independent test procedure in [START_HERE.md](START_HERE.md).

## Evidence provenance

- The developer's normal Windows PowerShell output reported **79 engine tests
  passed in 66.80 seconds**, followed by the complete verifier PASS line.
- The setup agent directly ran the original JSON starter's **five tests** and
  used a real MCP SDK client/server subprocess to discover ten tools and obtain
  `testDodoapp` status with zero memories.
- The developer performed the VS Code Copilot Agent conversations and pasted their
  results into the project conversation. The developer explicitly confirmed the
  initial remember and recall prompts were executed in **different chats**.
- The migration, six passing app tests, commit observation, replacement, and final
  recall below are recorded from those user-supplied agent results. They are not
  a newly repeated independent UI run or a retained raw protocol transcript.
- Antigravity and Cursor were not demonstrated in this recorded run. Their setup
  instructions are based on official documentation and still need independent tests.

## Original environment

Windows, Python 3.12.0, MCP 2.3.0, ChromaDB 1.5.9, sentence-transformers 6.1.0.
Engine: `C:\Users\moule\Desktop\MemoryLayer\0xMemory`.
Application: `C:\Users\moule\Desktop\MemoryLayer\testDodoapp`.
Agent: VS Code with GitHub Copilot; exact editor/model versions were not recorded.
The engine had local uncommitted changes, so no released engine SHA is asserted.

## Timeline and identifiers

| Checkpoint | Reported result |
| --- | --- |
| Initial status | Project testDodoapp; empty brain, all four category counts zero |
| Initial app commit | `ba7baeb5dd58e964fbcb038ec74cd067d859018f` |
| JSON decision | `mem-746bf126`, linked to storage.py and initial commit |
| Fresh-chat recall | Same ID and lab/inspectable-prototype rationale |
| Migration | SQLite tasks.db, transactional completion updates, one-time JSON import marker |
| App verification | Six tests passed; agent reported no Pylance errors and clean diff whitespace |
| Migration commit | `63549105ce9835c5213f789aab10e8aa94e18e40` |
| Commit files | README.md, storage.py, test_app.py; local commit, no push |
| Observation | mem-746bf126 affected through storage.py and marked stale |
| Evidence review | Agent inspected committed implementation and migration/restart tests |
| Replacement | `mem-5a804a2f` active; mem-746bf126 superseded by replacement |
| Final fresh-chat recall | SQLite rationale, mem-5a804a2f, migration evidence SHA |

The stored original rationale was JSON storage because the assessment lab had no
database service and the prototype should be inspectable. The replacement rationale
was SQLite for atomic updates and queryable task data without an external database
service, with one-time import preserving IDs and completion state.

## What this supports

The reported flow exercised persistent decisions across chats, explicit invalidation
linked to a code commit, reviewed replacement with preserved history, and retrieval
of the current replacement in a later chat. Commit observation and review were
explicitly requested; the system did not automatically infer the change from an edit.

## What remains unrecorded

Browser migration checks, exact editor/model versions, additional-editor handoffs,
raw MCP transcripts/screenshots, and a separate recall-only check between stale
marking and supersession were not supplied in the pasted results. The independent
guide asks testers to capture these rather than retroactively mark them passed.

No comparison baseline, repeated timing study, accuracy benchmark, or independent
assessment of generated code quality was performed by this single demonstration.
Use [TEST_REPORT_TEMPLATE.md](TEST_REPORT_TEMPLATE.md) for a new run; generate your
own memory IDs and commits rather than reusing this table.
