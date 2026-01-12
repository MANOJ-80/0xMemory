# 0xMemory

> 🧠 Cross-LLM Memory Layer for AI Agents

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Enabled-green.svg)](https://github.com/iterative/mcp)

**0xMemory** gives your AI coding agents specific, persistent, and portable memory.

Instead of explaining your project structure or coding preferences to every new chat session in Cursor, Claude, or Gemini, **0xMemory** stores this context in your repo where any agent can find it.

## ✨ Features

- **🧠 Persistent Memory**: Facts, decisions, and learnings are stored in human-readable Markdown files (`.0xmemory/memory/`).
- **🔌 Cross-Agent Compatible**: Works with **Cursor**, **Claude Desktop**, **Gemini**, and any [MCP](https://github.com/iterative/mcp)-compliant client.
- **🔍 vector Search**: Semantic retrieval helps agents find relevant past decisions and facts.
- **📄 Human Editable**: All memory is just Markdown. You can edit, delete, or version control it with Git.
- **🚀 Local First**: Your data stays in your repo. No external vector DBs required.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone and install
git clone https://github.com/manoj-80/0xMemory.git
cd 0xMemory
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Initialize a Brain

Go to your project directory and run:

```bash
cd /path/to/my/project
0xmemory init
```

This creates a `.0xmemory/` folder. Edit `.0xmemory/brain.md` to add your initial project context!

### 3. Connect your AI Agent

#### 🖱️ Cursor (IDE)

1. Go to **Settings > Cursor Settings > Models > MCP**.
2. Click **Add new MCP server**.
3. **Name**: `0xmemory`
4. **Type**: `SSE`
5. **URL**: `http://localhost:8000/sse`

_Note: You must have the server running:_

```bash
0xmemory serve --transport http
```

**JSON Configuration (Advanced)**
If you are configuring via a settings file (e.g., `settings.json` or generic MCP client config), use:

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

#### 🤖 Claude Desktop

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

## 🛠️ Usage

Once connected, your AI agent has access to these **Tools**:

- **`remember`**: Save important info.
  > "Remember that we use Poetry for dependency management."
- **`recall`**: Search past memories.
  > "What did we decide about database migrations?"
- **`extract`**: Auto-extract knowledge from a conversation.
  > "Extract the key decisions from these meeting notes..."

And these **Resources** (Context):

- **`brain://context`**: Reads your `brain.md` (Project Overview).
- **`brain://facts`**: List of all stored facts.
- **`brain://decisions`**: Log of architectural decisions.

## 🧠 The Separation of Powers

0xMemory is designed with a strict separation of concerns:

1.  **Human Territory (`.0xmemory/brain.md`)**

    - **Writable by**: YOU (The Human) only.
    - **Readable by**: The Agent.
    - **Purpose**: High-level strategy, mission statements, and "Supreme Laws" (e.g., "Always use TypeScript").
    - **Note**: The Agent is _forbidden_ from editing this file. It is your space to lead.

2.  **AI Territory (`.0xmemory/memory/*.md`)**
    - **Writable by**: The Agent (via `remember` tool).
    - **Readable by**: The Agent (via `recall` tool).
    - **Purpose**: Tactical details, API schemas, decision logs, and user preferences.

## 📁 Directory Structure

```text
.0xmemory/
├── brain.md              # Main project context (Human curated)
├── config.yaml           # Configuration
├── memory/               # AI memory (Auto-managed)
│   ├── facts.md
│   ├── decisions.md
│   ├── learnings.md
│   └── preferences.md
├── sessions/             # Chat session archives
└── .store/               # ChromaDB vector index (Git ignored)
```

## ⌨️ CLI Commands

| Command            | Description                                 |
| :----------------- | :------------------------------------------ |
| `0xmemory init`    | Initialize a brain in the current directory |
| `0xmemory serve`   | Start the MCP server (stdio or http)        |
| `0xmemory status`  | View brain statistics                       |
| `0xmemory add`     | Manually add a memory                       |
| `0xmemory forget`  | Delete a memory by ID                       |
| `0xmemory update`  | Update a memory's content                   |
| `0xmemory search`  | Search for memories                         |
| `0xmemory extract` | Extract knowledge from text                 |
| `0xmemory export`  | Export memories to JSON/CSV                 |
| `0xmemory rebuild` | Rebuild vector index from Markdown          |
| `0xmemory doctor`  | Run health checks on configuration          |

## 🧪 Real-World Testing

We have a detailed guide with 4 real-life scenarios (Context Switching, Decision Logs, etc.) to verify your setup.

👉 **[Read the Real-World Testing Guide](docs/testing_guide.md)**

> **Pro Tip:** Check the _Optimizing Token Usage_ section in the guide to learn how to scale to infinite memory using `.cursorignore`.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
