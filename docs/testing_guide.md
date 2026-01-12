# 0xMemory: Real-World Testing Guide

> **Status:** ✅ Ready for Use

This guide provides **real-life scenarios** to test the system's "memory" capabilities with your AI agents (Cursor, Claude, etc.).

---

## � How It Works (The Big Picture)

It can be confusing to understand where `0xMemory` lives. Here is the mental model:

1.  **It is a Package**: `0xMemory` is a command-line tool (like `git` or `npm`) you install on your computer.
2.  **It runs locally**: You run `0xmemory serve` in your terminal. This creates a local "Brain Server".
3.  **Cursor just "talks" to it**: Cursor (or Claude) connects to this local server. It does not install the code itself.

### The Workflow

For any new project, you follow these 3 steps (using the **local path** since we are in testing):

1.  **Init (Once per project)**:
    ```bash
    ../0xMemory/.venv/bin/0xmemory init --name "My Project"
    ```
2.  **Serve (Every time)**:
    ```bash
    ../0xMemory/.venv/bin/0xmemory serve --transport http
    ```
3.  **Connect (Once per Editor)**:
    - _Configure Cursor to listen to `localhost:8000`._

---

## 🧪 Real-Life Testing Scenarios

Use these scenarios to verify the system is creating value.

### Scenario 1: The "Context-Switch" Test

_Simulate coming back to a project after a month._

1.  **Setup**: Open Cursor w/ 0xMemory connected.
2.  **Action**: Tell the agent about a specific architectural preference.
    > "Remember that all our API endpoints must return standard JSON envelopes with 'data' and 'error' keys."
3.  **Verify**: Check `.0xmemory/memory/preferences.md` to see it saved.
4.  **Test**: Close the chat. Open a **new** chat window.
5.  **Prompt**: "Write a simple Hello World API endpoint for me."
6.  **Success**: The agent should generate code that includes the `data`/`error` envelope structure _without being asked_, because it recalled the preference.

### Scenario 2: The "Decision Log" Test

_Simulate onboarding a new developer (or agent)._

1.  **Action**: You are debating a tech choice.
    > "We are choosing `uv` over `poetry` because it is faster and written in Rust. Extract this decision."
2.  **Verify**: Agent should save this to `.0xmemory/memory/decisions.md`.
3.  **Test**: In a new session, ask:
    > "Why aren't we using Poetry?"
4.  **Success**: Agent recalls the rationale: "High speed and Rust implementation."

### Scenario 3: The "Knowledge Extraction" Test

_Simulate saving meeting notes._

1.  **Action**: Paste raw text into Composer.
    > "Notes from standup: The authentication service is moving to port 3001. The database password is now an env var named DB_PWD. We need to update the CI pipeline to use GitHub Actions v4."
2.  **Command**: "Extract all technical facts from these notes."
3.  **Verify**: Check `.0xmemory/memory/facts.md`.
4.  **Success**: It should have parsed out:
    - Auth service port: 3001
    - DB env var: DB_PWD
    - CI requirement: GitHub Actions v4

### Scenario 4: Manual Brain Surgery

_Simulate a human correcting the AI._

1.  **Action**: Open `.0xmemory/memory/facts.md` in your editor.
2.  **Edit**: Manually change a fact.
    - _Before_: "Auth service port: 3001"
    - _Change to_: "Auth service port: **8080**"
3.  **Test**: Ask Cursor: "What port does the auth service run on?"
4.  **Success**: Agent answers "**8080**". This proves the Markdown file is the source of truth.

---

## 🚀 Quick Setup Refresher

If you need to set this up on a new project (assuming your project is a sibling folder to `0xMemory`):

1.  **Initialize**:
    ```bash
    ../0xMemory/.venv/bin/0xmemory init
    ```
2.  **Serve**:
    ```bash
    ../0xMemory/.venv/bin/0xmemory serve --transport http
    ```
3.  **Connect Cursor**:
    - Name: `0xmemory`
    - Type: `SSE`
    - URL: `http://localhost:8000/sse`

---

## 🔧 Troubleshooting & Tips

### "Connection Refused" or Red Light in Cursor

- **Cause**: The server is not running or crashed.
- **Fix**: Restart the server.
  ```bash
  ../0xMemory/.venv/bin/0xmemory serve --transport http
  ```

### "Request Timed Out"

- **Cause**: Cursor sometimes loses the SSE connection if the computer sleeps.
- **Fix**: Go to **Cursor Settings > MCP**, click the "Refresh" (Visual Studio Code reload window) or simply delete and re-add the server.

### "Address already in use"

- **Cause**: Port 8000 is taken by another app.
- **Fix**: Run on a different port:
  ```bash
  ../0xMemory/.venv/bin/0xmemory serve --transport http --port 9000
  ```
  (Remember to update Cursor to `http://localhost:9000/sse`)

### Exporting Your Data

If you want to backup or analyze your memories, use the export command:

```bash
../0xMemory/.venv/bin/0xmemory export --format json --output my_backup.json
```

---

## 📂 Key Files to Watch

| File                     | Usage                                                            |
| :----------------------- | :--------------------------------------------------------------- |
| **`.0xmemory/brain.md`** | **Read-Only Context**. You write this. High-level project goals. |
| **`facts.md`**           | **Auto-Managed**. Agent writes specific technical details here.  |
| **`decisions.md`**       | **Auto-Managed**. Agent writes "Why we did X" here.              |
| **`preferences.md`**     | **Auto-Managed**. Agent writes "User likes X" here.              |

---

## ⚡ Advanced: Optimizing Token Usage

As your memory grows, you have a choice to make about **Context Window vs. Recall Speed**.

### Option A: The "Direct Access" Mode (Default)

Cursor reads `.0xmemory/*.md` files directly into its context window.

- **✅ Pros**: Very fast. No tool calls needed.
- **❌ Cons**: Uses more tokens. Can fill up context if you have 5,000+ memories.
- **Setup**: Do nothing. This is the default.

### Option B: The "Token Saver" Mode

Force Cursor to use the `recall` tool (Vector Search) instead of reading the files.

- **✅ Pros**: Zero token cost until needed. Scales to infinite memories.
- **❌ Cons**: Slightly slower (agent must decide to call a tool).
- **Setup**:
  1.  Create a `.cursorignore` file in your project root.
  2.  Add this line:
      ```text
      .0xmemory/memory/*.md
      ```
  3.  **Use Rules (Critical)**: Since the files are hidden, you MUST tell Cursor to use the tool. Create a `.cursorrules` file:
      ```markdown
      # 0xMemory Rules

      You have a long-term memory system called 0xMemory.
      If you cannot find information in the active files, you MUST use the `recall_0xMemory` tool to search for it.
      ALWAYS check `recall_0xMemory` before saying "I don't know".
      ```
      Now Cursor realizes: _"I can't see the file, but my rules say check the tool!"_
