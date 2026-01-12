# 0xMemory

> 🧠 **Cross-LLM Memory Layer for AI Agents** > _Give your AI Agent a persistent brain that lives in your repo._

[![PyPI version](https://img.shields.io/pypi/v/oxmemory.svg)](https://pypi.org/project/oxmemory/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Enabled-green.svg)](https://modelcontextprotocol.io)

**0xMemory** gives your AI coding agents (Cursor, Claude, Gemini) specific, persistent, and portable memory.

Instead of explaining your project structure or coding preferences to every new chat session, **0xMemory** stores this context in your repo where any agent can find it.

---

## ✨ Why 0xMemory?

- **🧠 Persistent**: Facts and decisions are stored in human-readable Markdown (`.0xmemory/memory/`).
- **🚀 Hybrid Architecture**:
  - **Local**: Vector search runs 100% locally on your machine (Privacy + Speed).
  - **Cloud**: Knowledge extraction uses your preferred LLM API (Groq, Gemini, OpenAI).
- **🔌 Universal**: Works with **Cursor**, **Claude Desktop**, and any MCP client.
- **� Git-Native**: Your memory is just files. Commit them, diff them, push them.

---

## 🚀 Quick Start

### 1. Installation

```bash
pip install oxmemory
```

### 2. Initialize a Brain

Go to your project directory and run:

```bash
cd /path/to/my/project
0xmemory init
```

This creates a `.0xmemory/` folder.

- **Action**: Edit `.0xmemory/brain.md` to add your high-level project goals.
- **Action**: (Optional) Add your API keys to `.env` if you want to use the `extract` tool.

### 3. Connect your AI Agent

First, start the Memory Server:

```bash
0xmemory serve --transport http
```

_(Note: The first run resolves a local AI model (~80MB). If it times out, just run it again.)_

#### 🖱️ For Cursor (IDE)

1.  Go to **Settings > Cursor Settings > Features > MCP**.
2.  Click **Add new MCP server**.
3.  **Name**: `0xmemory`
4.  **Type**: `SSE`
5.  **URL**: `http://localhost:8000/sse`

**Or add to your `config.json` (if using port 9000):**

```json
{
  "mcpServers": {
    "0xMemory": {
      "url": "http://localhost:9000/sse",
      "transport": "sse"
    }
  }
}
```

#### 🤖 For Claude Desktop

Add this to your `claude_desktop_config.json`:

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

## 🧠 Two Ways to Use It

0xMemory supports two distinct workflows depending on your style.

### Mode A: The "Disciplined" Agent (Local & Free)

_Best for: Coding sessions in Cursor/Claude._

You don't need any API keys for this. You just tell your Agent to remember things.

> **You**: "We strictly use `pydantic` v2 for all models."
>
> **You**: "Using the `remember` tool, save that preference."
>
> **Agent**: _Calls `remember` tool._ "Saved."

### Mode B: The "Lazy" Dump (Cloud Powered)

_Best for: Processing messy thoughts or meeting notes._

1.  Add an API key (e.g., `GROQ_API_KEY`, `GEMINI_API_KEY`) to your `.env` file.
2.  Dump text into the extractor:

```bash
0xmemory extract "We decided to switch to Postgres because Mongo was too retrieving complex relations."
```

3.  0xMemory will analyze it using the LLM and automatically save the **Decision** ("Switch to Postgres") and the **Reasoning** ("Mongo complex relations").

---

## 🛠️ Available Tools

Once connected, your Agent has these tools:

| Tool           | Description                                                          |
| :------------- | :------------------------------------------------------------------- |
| **`remember`** | Save a Fact, Decision, Learning, or Preference.                      |
| **`recall`**   | Search past memories using semantic search.                          |
| **`extract`**  | (Advanced) Read a block of text and extract knowledge automatically. |

And these **Resources** (Read-Only Context):

| Resource                | Description                      |
| :---------------------- | :------------------------------- |
| **`brain://context`**   | Your high-level `brain.md` file. |
| **`brain://facts`**     | List of all technical facts.     |
| **`brain://decisions`** | Log of architectural decisions.  |

---

## 📁 Directory Structure

```text
.0xmemory/
├── brain.md              # Main project context (Human curated)
├── memory/               # AI memory (Auto-managed)
│   ├── facts.md
│   ├── decisions.md
│   ├── learnings.md
│   └── preferences.md
├── sessions/             # Chat session archives
└── .store/               # Local Vector Index (Git ignored)
```

---

## 🔧 Troubleshooting

### First Run Timeout / Download Errors

On the very first run, 0xMemory downloads a local embedding model (~80MB) from Hugging Face.

- **Symptom**: `ReadTimeoutError` or `HTTPSConnectionPool` in logs.
- **Fix**: This is normal on slow connections. Just run the command again. It resumes where it left off.

### "Address already in use"

If port 8000 is taken:

```bash
0xmemory serve --port 9000
```

(Remember to update your Cursor config url to `http://localhost:9000/sse`)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
