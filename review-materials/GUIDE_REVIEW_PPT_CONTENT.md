# 0xMemory: guide-review presentation content

Purpose: present the working final-year prototype and demonstrate its memory lifecycle.
Suggested duration: 8–10 minutes of slides, followed by a 5-minute demonstration.
Use the **On-slide content** in PowerPoint. Use **Speaker notes** as your explanation.
Replace the name, department, guide, and date placeholders before presenting.

This presentation uses the recorded To-do lifecycle demonstration and the October 28 preference follow-up. It does not claim a new full lifecycle replay, a cross-model experiment, or a publication.

## Slide 1 — 0xMemory

### On-slide content

**A Code-Aware Persistent Memory Layer for AI Coding Assistants**

Final-Year Project: Working Prototype Demonstration

- Team: [Names and register numbers]
- Guide: [Guide name]
- Department / Institution: [Details]
- Review date: [Date]

### Speaker notes

“Our project helps AI coding assistants retain project decisions across conversations and manage those decisions when the supporting code changes. Today, we will demonstrate the working system using a To-do application in VS Code with GitHub Copilot.”

## Slide 2 — Problem statement

### On-slide content

- Project decisions can remain buried in previous conversations.
- A new conversation may lack the reason behind an implementation choice.
- Stored advice can become outdated as the code changes.
- Developers need relevant memories with visible evidence and history.

### Speaker notes

“Source code shows how a feature works, but it may not explain why the team chose that approach. For example, JSON storage may have been selected because the assessment lab has no database service. Later, the implementation may change to SQLite. A memory system must handle both persistence and the possibility that an earlier decision no longer applies.”

Do not claim that every existing assistant forgets everything. The problem is reliable, explicit project memory and maintenance of its evidence.

## Slide 3 — Project objectives

### On-slide content

- Save facts, decisions, learnings, and preferences for each project.
- Recall relevant information in a fresh conversation through MCP.
- Link memories to source files and Git commits.
- Flag affected memories for review after an observed commit.
- Preserve earlier decisions when a reviewed replacement becomes active.

### Speaker notes

“MCP stands for Model Context Protocol. It lets a compatible assistant call our memory tools. The memory belongs to the project and persists outside the conversation. We also record evidence so a reviewer can understand where a decision came from.”

## Slide 4 — System architecture

### On-slide content

| Component | Role |
| --- | --- |
| VS Code Copilot Agent | Requests memory operations through MCP |
| 0xMemory MCP server | Exposes remember, recall, and lifecycle tools |
| Project memory store | Saves readable Markdown entries and metadata |
| Search index | Supports semantic retrieval alongside keyword search |
| Git evidence and lifecycle logic | Tracks affected memories and review history |

### Speaker notes

“The editor launches the MCP server for the target project. A remember request saves an entry in that project's `.0xmemory` directory. A recall request searches the stored entries and returns eligible memories. The Git integration inspects an explicitly supplied commit to identify changes to linked files.”

The assistant performs coding tasks. 0xMemory supplies memory storage, retrieval, and lifecycle operations. The To-do application is a separate demonstration project.

## Slide 5 — Implementation and technology

### On-slide content

- Python implements the memory engine and command-line interface.
- Markdown stores project memories in a readable format.
- ChromaDB and local embeddings support semantic search.
- Semantic and keyword results contribute to memory retrieval.
- MCP connects the engine to compatible coding assistants.
- Git provides commit identifiers and changed-file evidence.

### Speaker notes

“We built on the existing 0xMemory foundation for storage, search, and MCP integration. Our prototype extends it with code-linked evidence, stale-memory handling, reviewed replacement, and decision history. We distinguish these additions from the underlying libraries and base implementation.”

“The memory files and index are local. An editor using a cloud AI model may still send the recalled content to that provider. Local storage alone does not mean the entire assistant workflow is offline.”

## Slide 6 — Memory record and lifecycle

### On-slide content

**A memory records:** content, type, ID, linked files, evidence commit, and lifecycle status.

| Status | Meaning |
| --- | --- |
| Active | Eligible for normal recall, subject to retrieval |
| Stale | Linked evidence changed and requires review |
| Superseded | A reviewed replacement preserves the previous decision as history |

### Speaker notes

“A file change is a reason to review a memory. It does not prove that the memory is false. After review, a still-valid memory can be verified. If the decision changed, we supersede the old entry with a new one. Normal recall excludes stale and superseded entries. History can be requested explicitly.”

“Commit observation is currently an explicit tool call. The prototype does not continuously watch uncommitted edits or automatically decide whether a natural-language statement is true.”

## Slide 7 — To-do application scenario

### On-slide content

**Initial decision: JSON file storage**

“The assessment lab has no database service, and we want an inspectable prototype.”

**Revised decision: SQLite storage**

“We need atomic task updates and queryable data without an external database service.”

Evidence file: `storage.py`

### Speaker notes

“Both choices are plausible for the application. The purpose of the example is to show how the memory follows a deliberate change in the project. JSON and SQLite are storage choices inside the To-do app. They should not be confused with the memory engine's Markdown files and ChromaDB index.”

“The SQLite implementation imports existing JSON tasks once, preserving IDs and completion state.”

## Slide 8 — Demonstration workflow

### On-slide content

1. Save the JSON decision with file and commit evidence.
2. Recall that decision in a separate conversation.
3. Migrate the app to SQLite, test, and commit.
4. Observe the commit and inspect the stale memory.
5. Review the implementation and supersede the old decision.
6. Recall the SQLite decision in another fresh conversation.

### Speaker notes

“For the recall steps, we ask the assistant to use only the MCP recall tool. We do not give it the previous conversation or ask it to read the memory files directly. We inspect the actual tool response, including the memory ID and evidence commit.”

“The initial rationale was kept out of source files and README during the original remember-and-recall demonstration. This made the MCP tool result the evidence for retrieving that rationale.”

## Slide 9 — Recorded demonstration results

### On-slide content

| Checkpoint | Recorded outcome |
| --- | --- |
| JSON decision saved | `mem-746bf126` |
| Recall in a different chat | Same decision and memory ID |
| SQLite migration observed | Original memory marked stale |
| Reviewed replacement | `mem-5a804a2f` active |
| Previous decision | Superseded with history preserved |
| Final fresh-chat recall | SQLite decision and evidence commit returned |

### Speaker notes

“These are identifiers from our recorded VS Code Copilot demonstration. A fresh run creates different IDs. The developer supplied the agent outputs and confirmed that the initial save and recall occurred in different chats. We should describe this as our recorded demonstration, not as an independent replication.”

“The recorded migration commit is `63549105ce9835c5213f789aab10e8aa94e18e40`. The original JSON commit is `ba7baeb5dd58e964fbcb038ec74cd067d859018f`.”

Evidence: [DEMO_RESULTS.md](../DEMO_RESULTS.md).

**October 28 follow-up for this slide:** Ordinary user requests produced visible
memory receipts: framework preference `mem-d1ffaf70`, new naming preference saved
as `mem-59c2d441`, and the same naming ID reported in a fresh chat. Both entries
were confirmed on disk. The earlier storage screenshot directly shows automatic
recall invocation. Preference receipts are assistant-generated, with raw tool
results collapsed. Show the [screenshots](evidence/2026-10-28/README.md) and state
these evidence limits. This is an observed workflow, not a measured reliability rate.

## Slide 10 — Verification evidence

### On-slide content

- Recorded Windows verification: **79 engine tests passed**.
- Recorded migrated To-do application: **6 tests passed**.
- Migration tests covered data preservation, persistence, and prevention of task resurrection.
- The demonstration exercised MCP recall across separate conversations.

**These results describe the recorded run, not a new verification of today's revision.**

### Speaker notes

“The engine verification output also reported successful dependency, CLI, real MCP client, embeddings, and semantic-evaluation checks. The six application tests belong to the To-do app, while the 79 tests belong to the memory engine at the recorded revision. These counts should not be combined into an accuracy percentage.”

“This demo establishes a functioning workflow. It does not measure improved coding accuracy or prove performance across all models and editors.”

Evidence: [DEMO_RESULTS.md](../DEMO_RESULTS.md). Consult [INTEGRATION_STATUS.md](../INTEGRATION_STATUS.md) for later checks and outstanding validation.

## Slide 11 — Current limitations and next work

### On-slide content

- Commit observation requires an explicit command or tool call.
- A changed linked file may trigger review even when the decision remains valid.
- Reviewers must check whether code actually supports a memory.
- The recorded client demonstration used VS Code Copilot.
- Next: repeat the demo independently and evaluate on more projects.

### Speaker notes

“Separate chats demonstrate persistent memory. They do not by themselves demonstrate a handoff between different models or clients. Setup instructions also exist for other clients, but we will report those as demonstrated only after observing their actual results.”

“For later research, we want to measure outdated-advice retrieval, retention of useful memories, and the effort required for review. The experimental research code is separate from the working demo and has not established those benefits on real-project studies.”

## Slide 12 — Project status

### On-slide content

**Working prototype demonstrated**

- Project decisions persist across conversations.
- Memories carry file and commit evidence.
- Explicit commit observation flags affected memories.
- Reviewed replacements preserve earlier decisions.

**Next milestone: a repeatable evaluation beyond the To-do example.**

### Speaker notes

“Our current deliverable is a working code-aware memory layer with a demonstrated decision lifecycle. Today, we are presenting the system and its behavior. Publication work will require broader experiments and comparison with existing approaches.”

“We would like feedback on whether the demonstrated workflow addresses the project problem and which evaluation cases should be prioritized next.”

---

## Live demo notes — existing project

Use these notes after Slide 8 or Slide 12. The existing project has already migrated to SQLite. Do not expect it to have zero memories or describe it as a fresh JSON baseline.

The original workspace folder is named `testDodoapp` and its configured MCP server was `0xmemory-dodo`. The application is a **To-do app**. New setup scripts use `testTodoapp` and `0xmemory-todo`. Use the server name actually configured in the editor.

### Before the review

1. Open the existing To-do project in VS Code.
2. Confirm the configured memory server is available.
3. Use one MCP client at a time for this project.
4. Keep this presentation and demo guides outside the app workspace.
5. Keep the recorded results available as backup if the live connection fails.

### Step A — show the connection

Paste into the agent chat, substituting the actual server name if different:

```text
Call the 0xmemory-dodo status tool. Show the actual project name,
brain path, and memory counts. Do not create or change any memories.
```

Explain: “The assistant is connected to the memory store for this project.”

### Step B — show fresh-chat recall

For the ordinary-request demonstration, first ask only:

```text
Which testing framework does our team prefer for this project?
```

Expect the existing `unittest` preference and a receipt naming `mem-d1ffaf70`.
In another fresh chat ask `What is our team's convention for naming test methods?`
and compare the receipt with `mem-59c2d441`. These are existing saved preferences,
so this rehearses retrieval rather than creating a new entry. Preserve actual
tool outputs when visible. The explicit storage prompt below remains useful for
a diagnostic check if ordinary tool selection fails.

Open a new chat and paste:

```text
Use only the 0xmemory-dodo recall tool to answer:
What is our current task storage decision, and why?
Use file_paths ["storage.py"] and include_history false.
Show the memory ID and evidence commit from the tool result.
Do not read files, guides, or previous chats. Do not change memories.
```

Expected for the unchanged recorded project: SQLite at `data/tasks.db`, the atomic-update/queryability rationale, memory `mem-5a804a2f`, and the migration commit. If the actual project has changed since the recorded run, report the actual result and investigate any discrepancy.

### Step C — show preserved history

```text
Use the 0xmemory-dodo recall tool with file_paths ["storage.py"]
and include_history true to inspect our task storage decisions.
Show the returned IDs and lifecycle statuses, clearly distinguishing
the current SQLite decision from the superseded JSON decision.
Do not create, verify, update, or supersede any memory.
```

If recall does not return both entries, use the `list` tool to inspect their statuses. Retrieval is relevance-based and is not guaranteed to enumerate all history.

Explain: “We preserve the original decision, but normal recall treats the reviewed replacement as the current memory.”

### Step D — show the application and evidence

- Show the running To-do app if it has been rehearsed successfully.
- Add a demonstration task, complete it, and reload to show the visible behavior.
- Show `storage.py` using SQLite and the recorded migration-test output.
- Describe an app restart test as performed only if you actually perform it or show its recorded result.

This short presentation demonstrates the existing final state and preserved history. It does not replay the earlier stale transition live. Show that transition using recorded evidence, or rehearse the full flow in a separate fresh project before presenting it as a live sequence.

For a complete fresh replay, use [QUICKSTART_DEMO.md](../QUICKSTART_DEMO.md) and [DEMO_FLOW.md](../DEMO_FLOW.md). Do not reset or delete the existing demonstration's memories to make it look fresh.

## Likely guide questions and suggested answers

### What is the main contribution of your implementation?

“We extend a persistent memory foundation with code-linked evidence and a decision lifecycle. An explicit commit inspection flags affected memories, and review can verify or replace a decision while preserving its history. We are not yet claiming that this is a novel research algorithm.”

### How is this different from storing a conversation?

“We store individual project memories with types, IDs, evidence, and lifecycle status. The assistant can retrieve selected entries through a tool instead of receiving an entire conversation.”

### Does stale mean incorrect?

“No. Stale means the linked evidence changed and needs review. A harmless edit can also trigger that status. The reviewer decides whether to verify or replace the memory.”

### Does the system automatically watch Git?

“Currently, we explicitly call observe_commit after a commit. Continuous monitoring and uncommitted-edit tracking are not part of this demonstration.”

### Can it work with other AI assistants?

“MCP provides a common integration interface, and we have configuration guides for multiple clients. Our recorded interactive demonstration used VS Code Copilot. Other client and model handoffs require their own verification.”

### Does it train the model or change its weights?

“No. It supplies external project context through memory tools. It does not fine-tune the coding model.”

### Why use a To-do app?

“It gives us a small, inspectable change with a clear decision history. JSON-to-SQLite migration lets us demonstrate an old decision, a code change, review, and replacement without a large application obscuring the memory behavior.”

### Have you proved that coding quality improves?

“Not through this demonstration. We have demonstrated functionality. A controlled comparison across more tasks is needed to measure coding quality, time savings, or reduced use of outdated advice.”

## Supporting project documents

- [Recorded demonstration and evidence provenance](../DEMO_RESULTS.md)
- [System overview and implementation boundaries](../README.md)
- [Fresh setup](../QUICKSTART_DEMO.md)
- [Full demonstration prompts](../DEMO_FLOW.md)
- [Verification status and outstanding checks](../INTEGRATION_STATUS.md)
- [Independent tester report](../TEST_REPORT_TEMPLATE.md)

## Presenter checklist

- Fill in team, guide, institution, and review date.
- Rehearse the short existing-project demo before the meeting.
- Capture actual tool responses and keep memory IDs visible.
- Label previously recorded evidence clearly.
- Keep the original JSON and replacement SQLite memory IDs distinct.
- Present cross-chat persistence as demonstrated and cross-client behavior as pending unless newly tested.
- Avoid claims of 100% accuracy, guaranteed correctness, or publication acceptance.
