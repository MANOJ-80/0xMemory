# 0xMemory demo: memory that survives chats and code changes

A short, presenter-ready walkthrough of the core product. One real coding task
runs across several chats: the agent saves a storage decision, continues the task
in a fresh session, migrates the code, notices that the saved decision needs
review, and replaces it without losing the earlier history.

**Running time:** about 8 minutes. Keep the agent's memory activity visible.

## Before you start

From the repository root, prepare a fresh demo project:

```bash
# Ubuntu
python3 scripts/setup-and-run.py --project ../memory-demo
```

```powershell
# Windows PowerShell
py scripts/setup-and-run.py --project ..\memory-demo
```

Add `--skip-install` if dependencies are already installed. Then:

1. Open the generated app folder in VS Code (not the engine folder).
2. Trust the project and start **0xmemory-todo** from the MCP server list.
3. Keep this guide outside the app folder so the agent cannot read it.
4. Use one MCP client at a time.

**Connection check.** In the first chat, ask:

> What project are you connected to, and how many memories do you currently have?

Confirm the project name and zero memories before continuing. If the agent
reports a different project, stop and reopen the app folder.

## Act 1 — Make a decision (60 seconds)

> Before we change task storage, look at `storage.py`. For this prototype, keep
> persistence in a local JSON file because it must work without a database
> service and stay easy to inspect. Remember that decision and the reason, then
> summarize what you found.

**What to watch for:** the agent inspects the code, saves the decision with its
rationale, and ties it to the current code. Its answer may end with a short
`Memory: saved ...` receipt. Do not read the full identifier aloud.

## Act 2 — Recall it in a fresh chat (60 seconds)

Start a **new chat** in the same project:

> I'm picking up the task storage work in a new chat. What did we decide about
> storage, and why? Check the current code before answering.

**What to watch for:** the agent recalls the JSON decision and its reason without
the old conversation being pasted in. It should still check the current code
rather than treating memory as proof.

## Act 3 — Start the task, then continue in another chat (2 minutes)

Still in that chat, ask for only the first part of the migration:

> Start the task storage migration, but only do the first part now: switch
> `TaskStore` to SQLite using Python's built-in `sqlite3`, keep the existing
> interface and API unchanged, and import the JSON tasks once without changing
> their IDs or completion state. Do not add the new tests or update the README
> yet. Leave the work checkpointed so I can continue in a new chat.

**What to watch for:** the agent implements only that part and leaves a resumable
checkpoint with the remaining work. It should not claim the whole migration is
finished.

Now open a **fresh chat** and ask:

> I'm continuing the task storage migration. Pick up where we left off.

**What to watch for:** the agent finds the earlier checkpoint, restates the
objective and remaining steps, then completes the tests and README from the
current files instead of restarting the whole task.

## Act 4 — Change the code and trigger review (90 seconds)

> Review the migration, then commit only the source, tests, and README locally.
> Do not push. After committing, check whether any saved project memory needs
> review.

**What to watch for:** the agent commits the reviewed change and flags the old
JSON decision for review because its supporting code changed. The memory is
questioned, not silently trusted or deleted.

## Act 5 — Replace the decision, keep the history (90 seconds)

> The storage claim is flagged. Check the new implementation and tests. If the
> SQLite change supports a new decision, replace the old memory and keep the old
> one available as history. Tell me what changed and why.

**What to watch for:** the agent inspects the committed evidence, stores the new
SQLite decision, marks it active, and preserves the earlier JSON decision as
superseded history. No long IDs or hashes need to be shown.

## Act 6 — A final fresh-chat check (60 seconds)

Open one last **new chat**:

> What is our current task storage approach and why? Also, what did we use before
> the migration?

**What to watch for:** the agent answers with the current SQLite decision and its
rationale, then distinguishes the earlier JSON decision as history. This proves
recall works across sessions and that history is still available after a change.

## Close (30 seconds)

Show the outcome, not the plumbing:

- Decisions persist across separate chats.
- An unfinished task resumes in a new session.
- A code change makes outdated evidence reviewable.
- Replacing a decision keeps its earlier version.
- The agent reports what it actually recalled or saved.

Do not read memory IDs, commit hashes, or raw tool output aloud during the demo.
If the agent shows them, let them stay in the transcript and keep the narration
focused on the behavior.

## Presenter notes

- Use a new chat for Acts 2, 3 (second half), and 6. A new chat is what makes the
  persistence test believable.
- Do not tell the agent which memory tools to call; the project instructions
  already guide it to recall, save, checkpoint, and review memory when relevant.
- If the agent asks for confirmation, confirm the decision or the migration, not
  the internal tool choice.
- If recall returns a warning after the commit, do not call the memory false.
  Explain that the evidence changed and review is required.
- If the agent skips a step, ask for the outcome in plain language, for example:
  "Can you check whether the saved decision is still supported by the current
  code?"
- Choose a fresh project folder for each run. Do not reuse memories from an
  earlier demonstration.

For the longer evidence-collection procedure, use the generated `DEMO_FLOW.md` in
the setup evidence folder.
