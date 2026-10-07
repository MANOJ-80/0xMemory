# Independent tester report

Copy this file outside the Dodo agent workspace before filling it in. Use PASS, FAIL, or NOT RUN for every check; do not treat an unanswered check as success.

## Environment

| Field | Value |
| --- | --- |
| Tester and date | |
| OS and version | |
| Linux distribution / architecture (if applicable) | |
| Execution context (native Windows / native Ubuntu / WSL / other) | |
| Setup guide followed | |
| Engine clone URL / branch | |
| Full engine commit SHA | |
| Any uncommitted engine changes (`git status --short`) | |
| Python version and absolute executable | |
| MCP / ChromaDB / sentence-transformers versions | |
| Dependency snapshot path | |
| Editor / version / agent model | |
| App absolute path | |
| Brain absolute path | |
| First model download succeeded | |

## Run identifiers

| Identifier | Actual value from this run |
| --- | --- |
| INITIAL_SHA | |
| OLD_ID | |
| NEW_SHA | |
| NEW_ID | |

## Checks

| Check | Expected | PASS / FAIL / NOT RUN | Actual result / evidence filename |
| --- | --- | --- | --- |
| pip check | No broken requirements | | |
| Embedding preparation | Real model shape (1, 384) | | |
| Full engine verification | All tests + demo + semantic evaluation succeed | | |
| Starter app | Five tests pass | | |
| MCP discovery | Ten tools; correct project/path | | |
| Initial status | Zero memories | | |
| Browser JSON app | Add/complete/delete; restart persistence | | |
| Remember | OLD_ID active; linked storage.py and INITIAL_SHA | | |
| Fresh Chat B | Actual recall returns OLD_ID + rationale | | |
| SQLite migration tests | Preserve IDs/completion; no resurrection; persistence | | |
| Browser after migration | Original tasks/states survive; deleted task stays absent | | |
| Local commit | NEW_SHA includes reviewed migration files only | | |
| observe_commit | OLD_ID stale through storage.py | | |
| Normal recall before review | OLD_ID excluded | | |
| Evidence review | Recorded statement matches committed code/tests | | |
| Supersession | OLD_ID superseded; NEW_ID active; links preserved | | |
| Fresh Chat D | Actual recall returns NEW_ID + NEW_SHA + SQLite rationale | | |
| History retrieval | Old/new entries distinguished by status | | |
| Editor/server restart | Current decision persists | | |
| Dashboard (optional) | Visible statuses/history | | |

## Additional editors (optional)

Stop the previous MCP server before each test. Use the same app and brain.

| Editor/version/model | Actual status tool result | Recalled NEW_ID / NEW_SHA | Result and evidence |
| --- | --- | --- | --- |
| VS Code Copilot | | | |
| Antigravity | | | |
| Cursor | | | |

## Failures and deviations

For each failure record: step number, command or prompt, working directory,
first exception/tool error, relevant log excerpt, expected/actual behavior,
fix attempted, and result after retry. Do not include credentials in shared logs.

Record any changed prompts, extra memories, skipped tests, keyword-only fallback,
or source-file reads during a recall-only checkpoint.

## Conclusion

- Checks passed:
- Checks failed:
- Checks not run:
- Functional claims supported by this run:
- Remaining limitations or questions:

Do not infer retrieval accuracy percentages, coding productivity improvements,
or universal client compatibility from one functional demonstration.
