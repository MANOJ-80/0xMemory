# 0xMemory

> 🧠 Terminal-first AI agent with persistent memory - turns your project into a living brain

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is 0xMemory?

0xMemory is a terminal-first AI agent that transforms your project folder (Git repo) into a **living brain** with persistent memory. Unlike traditional AI assistants that forget everything between sessions, 0xMemory:

- 📝 **Remembers everything** - Facts, decisions, and learnings persist in human-editable Markdown files
- 🔍 **Retrieves contextually** - Semantic search finds relevant memories from your documents
- 🤖 **Reasons with context** - LLM responses are grounded in your project's accumulated knowledge
- 📜 **Tracks changes** - Session logs and changelogs make your AI interactions reproducible

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/0xMemory.git
cd 0xMemory

# Install with Poetry
poetry install

# Or with pip
pip install -e .
```

### Initialize Your Brain

```bash
# Navigate to your project
cd your-project

# Initialize 0xMemory
0xmemory init

# Or use the alias
oxmemory init
```

This creates a `.0xmemory/` directory with:

```
.0xmemory/
├── config.yaml           # Configuration
├── brain.md              # Main project context (edit this!)
├── memory/
│   ├── facts.md          # Learned facts
│   ├── decisions.md      # Decision log
│   ├── learnings.md      # Lessons learned
│   └── preferences.md    # Your preferences
├── documents/            # Documents for RAG
├── vectordb/             # ChromaDB storage
└── changelog.md          # Session history
```

### Start Chatting

```bash
0xmemory chat
```

Your AI now has access to your project context and will remember everything across sessions!

## Features

### 🧠 Persistent Memory

Edit `.0xmemory/brain.md` to give your AI context about your project:

```markdown
# 🧠 Project Brain

## Project Overview

This is a FastAPI backend for our e-commerce platform...

## Key Components

- `api/` - REST API endpoints
- `models/` - SQLAlchemy models
- `services/` - Business logic

## Conventions

- Use snake_case for Python files
- All endpoints need auth decorators
```

### 📥 Document Ingestion

Add your documentation to the brain:

```bash
# Ingest a single file
0xmemory ingest docs/architecture.md

# Ingest an entire directory
0xmemory ingest docs/ --recursive
```

### 🔍 Semantic Search

Search through your memories:

```bash
0xmemory search "how does authentication work"
```

### ⚙️ Configuration

Customize your setup in `.0xmemory/config.yaml`:

```yaml
llm:
  provider: gemini # gemini, openai, anthropic, ollama
  model: gemini-2.0-flash
  temperature: 0.7

memory:
  embedding_model: all-MiniLM-L6-v2
  chunk_size: 512
  max_retrieval: 5

git:
  commit_on_end: true
  commit_prefix: "[0xMemory]"
```

## Commands

| Command          | Description                                     |
| ---------------- | ----------------------------------------------- |
| `init`           | Initialize a new brain in the current directory |
| `chat`           | Start an interactive chat session               |
| `status`         | Show brain statistics                           |
| `ingest <path>`  | Add documents to the brain                      |
| `search <query>` | Search memories                                 |
| `config --show`  | Show current configuration                      |

## Environment Variables

Set your API keys:

```bash
# Google Gemini (default)
export GEMINI_API_KEY=your-key

# OpenAI
export OPENAI_API_KEY=your-key

# Anthropic
export ANTHROPIC_API_KEY=your-key
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         0xMemory                            │
├─────────────────────────────────────────────────────────────┤
│   CLI (typer)  ◄──►  Context Files (Markdown)              │
│        │                                                    │
│   ┌────▼────────────────────────────────────────┐          │
│   │           Orchestration (Brain)              │          │
│   └────┬────────────────────────────────────────┘          │
│        │                                                    │
│   ┌────▼────────────────────────────────────────┐          │
│   │              Memory Layer                    │          │
│   │  ChromaDB + Embeddings + Retrieval          │          │
│   └────┬────────────────────────────────────────┘          │
│        │                                                    │
│   ┌────▼────────────────────────────────────────┐          │
│   │           LLM Layer (LiteLLM)                │          │
│   │   Gemini / OpenAI / Claude / Ollama         │          │
│   └─────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with ❤️ for developers who want their AI to actually remember them.
