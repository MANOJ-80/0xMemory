# To-do memory demonstration: agent prompts

Setup does not complete this interactive test. Open only the app folder in your
agent, keep this guide outside that folder, and use one MCP client at a time.
Generated copies replace {{PROJECT}} and {{TEST_COMMAND}} with your actual values.
Run the generated run-app script, open http://127.0.0.1:8090, add two tasks,
complete one, restart, and check persistence. Stop the app before migration.

## 1. Connection check

```text
Call 0xmemory-todo status. Report the project, brain path, and counts.
Expect project {{PROJECT}} and zero memories. Stop if they differ.
Show the actual tool result; do not infer it from source files.
```

## 2. Chat A: remember

```text
Inspect storage.py and obtain the full Git HEAD SHA.
Use 0xmemory-todo remember to save this developer-provided decision:
"We chose JSON file storage for tasks because the assessment lab has no
database service and we want an inspectable prototype."
Use type decision, file_paths ["storage.py"], and commit_sha set to that SHA.
Show the returned memory ID and SHA. Do not write the rationale into source,
README, AGENTS.md, or any other file.
```

Record OLD_ID and INITIAL_SHA in TEST_REPORT.md outside the app.

## 3. Chat B: new conversation

```text
Use only 0xmemory-todo recall to explain our chosen task storage and why.
Use file_paths ["storage.py"] and include_history false. Show ID and commit.
Do not read files, previous chats, or setup guides.
```

Pass: actual recall returns OLD_ID and the lab/inspectable-prototype rationale.

## 4. Chat C: migrate implementation

```text
Recall our task storage decision using 0xmemory-todo, then migrate the app
from JSON to SQLite. Our new rationale is atomic task updates and queryable
data without an external database service.
Preserve the TaskStore API, endpoints, and UI. Store tasks at data/tasks.db.
Import tasks.json once, preserving IDs and completion state. Mark migration
complete even if JSON is absent. Restarts must not duplicate or resurrect tasks.
Add migration, persistence, and no-resurrection tests; update README.
Run the app tests from this directory with:
{{TEST_COMMAND}}
Show results and changed files. Do not commit or modify memories yet.
```

Review tests/diff, restart the app, confirm original tasks and state survived,
then delete a task and restart to verify it stays absent. Fix failures first.

## 5. Commit reviewed changes

```text
Commit only the reviewed migration source, tests, and README locally with
message "Migrate task storage from JSON to SQLite". Do not push, commit task
data/configs/memories, or change memories. Use per-command identity
user.name "Todo Demo" and user.email "demo@example.invalid" if needed;
do not change global Git configuration. Show the full new SHA.
```

Record NEW_SHA. Replace OLD_ID and NEW_SHA below with the returned values.

## 6. Observe and check stale exclusion

```text
Call 0xmemory-todo observe_commit with commit NEW_SHA.
Use list to inspect OLD_ID and show its status. Recall our task storage decision
with file_paths ["storage.py"] and include_history false.
Do not verify, supersede, or create memories yet.
```

Pass: OLD_ID becomes stale and does not appear in normal recall.

## 7. Review evidence and supersede

```text
Inspect storage.py and tests at NEW_SHA. If they support this decision,
call 0xmemory-todo supersede_memory with id OLD_ID, commit NEW_SHA,
file_paths ["storage.py"], and a note explaining the actual evidence reviewed.
Content: "Tasks now use SQLite at data/tasks.db for atomic updates and queryable
data without an external database service. JSON tasks are imported once,
preserving IDs and completion state."
If unsupported, explain the mismatch instead. Show the replacement memory ID.
Use list to confirm the old entry is superseded and its replacement is active.
Preserve the old entry.
```

Record NEW_ID. Do not paste historical IDs from earlier demonstrations.

## 8. Chat D: fresh recall

```text
Use only 0xmemory-todo recall: What is our current task storage decision and why?
Use file_paths ["storage.py"] and include_history false. Show memory ID and commit.
Do not read files, guides, or previous chats.
```

Pass: SQLite, new rationale, NEW_ID, and NEW_SHA. Request history separately with
include_history true and distinguish obsolete JSON from the current decision.

## 9. Cross-client handoff

Stop the first client's MCP server/session, open the SAME app folder in the other
client, and repeat Chat D. Do not create another brain or copy memories. Record
client versions and actual tool results. Separate chats test persistence;
switching clients additionally tests the shared memory integration.

Capture screenshots, IDs, commits, and test output in the evidence folder.
Mark all unrun checks NOT RUN. Setup PASS is not proof of agent recall.
