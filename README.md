<p align="center">
  <h1 align="center">🧠 0xMemory</h1>
  <p align="center">
    <strong>Give your AI a brain that lives in your repo.</strong>
  </p>
  <p align="center">
    <a href="https://pypi.org/project/oxmemory/"><img src="https://img.shields.io/pypi/v/oxmemory.svg" alt="PyPI"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
    <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-Enabled-green.svg" alt="MCP"></a>
  </p>
</p>

---

**0xMemory** is a cross-LLM memory layer that gives AI coding agents (Cursor, Claude, Gemini) persistent, portable memory.

Stop explaining your project to every new chat session. 0xMemory stores context in human-readable Markdown files that any agent can find.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│   You: "Remember that we use PostgreSQL for auth."          │
│                          ↓                                  │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              0xMemory MCP Server                    │  │
│   │   Saves to Markdown → Indexes in Vector DB          │  │
│   └─────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│   Later: "What database do we use?"                         │
│   Agent: "You use PostgreSQL for auth." ✅                  │
└─────────────────────────────────────────────────────────────┘
```

| Feature        | Description                                                   |
| -------------- | ------------------------------------------------------------- |
| **Persistent** | Facts and decisions stored in `.0xmemory/memory/` as Markdown |
| **Private**    | Vector search runs 100% locally on your machine               |
| **Portable**   | Works with Cursor, Claude Desktop, and any MCP client         |
| **Git-Native** | Your memory is just files. Commit, diff, and push them.       |

---

## Quick Start

### Step 1: Set Up Environment

```bash
# Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install 0xMemory
pip install oxmemory
```

### Step 2: Initialize

```bash
cd /path/to/your/project
0xmemory init
```

This creates a `.0xmemory/` folder. Edit `.0xmemory/brain.md` to describe your project.

### Step 3: Start the Server

```bash
0xmemory serve --transport http
```

> **Note**: First run downloads a small embedding model (~80MB). If it times out, just run it again.

### Step 4: Connect Your AI

#### Cursor IDE

Add to your MCP config (`.cursor/mcp.json` or via Settings → Features → MCP):

```json
{
  "mcpServers": {
    "0xMemory": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    }
  }
}
```

#### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "0xmemory": {
      "command": "0xmemory",
      "args": ["serve"],
      "cwd": "/absolute/path/to/your/project"
    }
  }
}
```

---

## Usage

### Disciplined Mode (Local, Free)

Tell your agent what to remember. No API keys required.

```
You: "We use Pydantic v2 for all models. Remember that."
Agent: ✅ Memory saved.
```

### Lazy Mode (Cloud-Powered)

Dump messy notes, 0xMemory extracts the knowledge for you.

1. Add an API key to `.env` (e.g., `GROQ_API_KEY`)
2. Run:
   ```bash
   0xmemory extract "We decided to switch to Postgres because Mongo was too slow for complex joins."
   ```
3. 0xMemory saves:
   - **Decision**: Switch to Postgres
   - **Reasoning**: Mongo slow for complex joins

---

## LLM Providers

The `extract` tool uses an LLM to parse knowledge from text. Configure via `.env`:

| Provider       | Env Variable         | Free Tier      | Notes               |
| -------------- | -------------------- | -------------- | ------------------- |
| **Groq**       | `GROQ_API_KEY`       | 14,400 req/day | Recommended for dev |
| **Gemini**     | `GEMINI_API_KEY`     | 20 req/day     | Save for demos      |
| **OpenRouter** | `OPENROUTER_API_KEY` | Pay-as-you-go  | Many models         |
| **Ollama**     | `OLLAMA_API_BASE`    | Unlimited      | Fully local         |

**Example `.env`:**

```bash
# Pick one (or more for fallback)
GROQ_API_KEY=gsk_xxx...
GEMINI_API_KEY=AIza...

# For remote Ollama (e.g., Google Colab + ngrok)
OLLAMA_API_BASE=https://your-tunnel.ngrok.io
```

0xMemory tries providers in order: Ollama → Groq → OpenRouter → Gemini.

---

## Available Tools

Once connected, your AI agent has access to these MCP tools:

| Tool       | What It Does                                    |
| ---------- | ----------------------------------------------- |
| `remember` | Save a Fact, Decision, Learning, or Preference  |
| `recall`   | Search memories using semantic search           |
| `list`     | List all memories with optional filters         |
| `forget`   | Remove a memory by ID                           |
| `update`   | Update an existing memory                       |
| `status`   | Get brain statistics                            |
| `extract`  | Auto-extract knowledge from text (requires LLM) |

And these read-only resources:

| Resource            | Content                        |
| ------------------- | ------------------------------ |
| `brain://context`   | Your project's `brain.md` file |
| `brain://facts`     | All stored technical facts     |
| `brain://decisions` | Log of architectural decisions |
| `brain://full`      | Combined full context          |

---

## Project Structure

After running `0xmemory init`, your project gets a `.0xmemory/` folder:

```
.0xmemory/
├── brain.md           # 👈 Your project context (edit this!)
├── config.yaml        # Server and LLM settings
├── memory/            # AI-managed memory files
│   ├── facts.md       # Technical facts ("API uses port 3000")
│   ├── decisions.md   # Architectural decisions with reasoning
│   ├── learnings.md   # Lessons learned, gotchas, tips
│   └── preferences.md # Coding style preferences
├── documents/         # (Optional) Docs for RAG ingestion
├── sessions/          # Chat session history archives
└── .store/            # Vector database (auto-generated, gitignored)
    └── chroma/        # ChromaDB embeddings for semantic search
```

### What Each File Does

| File/Folder   | Purpose                                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------------------------- |
| `brain.md`    | **You write this.** High-level project description, architecture, goals. The AI reads this first.                   |
| `config.yaml` | Configuration for LLM providers, embedding models, and server settings.                                             |
| `memory/*.md` | **AI writes these.** Extracted knowledge from your conversations. Human-readable and editable.                      |
| `documents/`  | Drop markdown/text files here for document-based retrieval (RAG).                                                   |
| `sessions/`   | Archived chat sessions for context continuity.                                                                      |
| `.store/`     | Local vector database (ChromaDB). Enables semantic search. Auto-generated, safe to delete (rebuilds from markdown). |

---

## CLI Reference

| Command                      | Description                                          |
| ---------------------------- | ---------------------------------------------------- |
| `0xmemory init`              | Create a new brain in current directory              |
| `0xmemory serve`             | Start MCP server (add `--transport http` for Cursor) |
| `0xmemory status`            | Show brain statistics                                |
| `0xmemory add "..."`         | Manually add a memory                                |
| `0xmemory search "..."`      | Search memories                                      |
| `0xmemory forget <id>`       | Delete a memory by ID                                |
| `0xmemory update <id> "..."` | Update a memory's content                            |
| `0xmemory extract "..."`     | Extract knowledge via LLM                            |
| `0xmemory export`            | Export memories to JSON/CSV                          |
| `0xmemory rebuild`           | Rebuild vector index from Markdown                   |
| `0xmemory doctor`            | Check configuration health                           |
| `0xmemory config --show`     | View current configuration                           |

**Useful flags:**

```bash
0xmemory serve --transport http --port 9000  # Custom port
0xmemory serve --debug                        # Verbose logging
0xmemory export -o backup.json                # Export to JSON
0xmemory export -o data.csv --type fact       # Export facts to CSV
```

---

## Advanced: Token Optimization

As your memory grows, you can optimize how Cursor uses it.

### Default Mode (Direct Access)

Cursor reads `.0xmemory/*.md` files directly into its context window.

- ✅ Fast - no tool calls needed
- ❌ Uses tokens - can fill context with large memories

### Token Saver Mode

Force Cursor to use the `recall` tool (vector search) instead of reading files directly. This scales to unlimited memories with zero token cost until needed.

**Step 1:** Create `.cursorignore` in your project root:

```text
.0xmemory/memory/*.md
```

**Step 2:** Create `.cursorrules` to tell Cursor about the memory tool:

```markdown
# 0xMemory Rules

You have a long-term memory system called 0xMemory.
When you need project context or past decisions, use the `recall` tool to search for it.
ALWAYS check `recall` before saying "I don't know".
```

Now Cursor won't read the files directly, but will use semantic search when it needs information.

---

## Troubleshooting

| Problem                    | Solution                                                |
| -------------------------- | ------------------------------------------------------- |
| **First run timeout**      | Normal on slow connections. Download resumes on retry.  |
| **Port 8000 in use**       | Use `0xmemory serve --port 9000` and update your config |
| **Model download stuck**   | Check internet connection, then run again               |
| **Connection refused**     | Make sure `0xmemory serve` is running in a terminal     |
| **Cursor shows red light** | Restart the server, then refresh MCP in Cursor settings |

**Health check:** When running in HTTP mode, visit `http://localhost:8000/health` to verify the server is up.

---

## License

[MIT](LICENSE)

---

<p align="center">
  <sub>Built for developers who want their AI to actually remember things.</sub>
</p>
