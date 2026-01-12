# 0xMemory Prerequisites & Learning Guide

> **Purpose:** Everything you need to know before building 0xMemory  
> **Time to Learn:** 1-2 weeks (depending on your background)

---

## Table of Contents

1. [Quick Overview](#quick-overview)
2. [Required Knowledge](#required-knowledge)
3. [Technologies & Libraries](#technologies--libraries)
4. [API Keys & Accounts](#api-keys--accounts)
5. [Development Environment](#development-environment)
6. [Learning Resources](#learning-resources)
7. [Checklist](#checklist)

---

## Quick Overview

### What We're Building

```
┌─────────────────────────────────────────────────────────────┐
│                      0xMemory                               │
│         Local MCP Server for Cross-LLM Memory               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INPUT:  Conversations from Claude/Gemini/Cursor            │
│          ↓                                                  │
│  PROCESS: Extract facts → Embed → Store → Search            │
│          ↓                                                  │
│  OUTPUT: Persistent memory that works across all LLMs       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Technologies at a Glance

| Layer          | Technology                   | What to Learn                 |
| -------------- | ---------------------------- | ----------------------------- |
| **Protocol**   | MCP (Model Context Protocol) | How AI tools communicate      |
| **Storage**    | ChromaDB, SQLite             | Vector databases, embeddings  |
| **Embeddings** | sentence-transformers        | Converting text to vectors    |
| **Language**   | Python 3.11+                 | Async programming, type hints |
| **CLI**        | Typer, Rich                  | Building beautiful CLIs       |

---

## Required Knowledge

### Must Know (Core)

| Topic            | Proficiency Needed | Why                              |
| ---------------- | ------------------ | -------------------------------- |
| **Python**       | Intermediate       | Main language for the project    |
| **Async/Await**  | Basic              | MCP uses async communication     |
| **JSON**         | Basic              | MCP protocol is JSON-RPC         |
| **Git**          | Basic              | Version control for memory files |
| **Command Line** | Comfortable        | Terminal-first design            |

### Should Know (Helpful)

| Topic                                    | Proficiency | Why                               |
| ---------------------------------------- | ----------- | --------------------------------- |
| **Vector Embeddings**                    | Conceptual  | How semantic search works         |
| **RAG (Retrieval Augmented Generation)** | Conceptual  | Core pattern for memory retrieval |
| **SQLite**                               | Basic       | Metadata storage                  |
| **YAML**                                 | Basic       | Configuration files               |

### Nice to Know (Advanced)

| Topic                | Why                      |
| -------------------- | ------------------------ |
| **Knowledge Graphs** | Future GraphRAG features |
| **FastAPI**          | HTTP transport mode      |
| **Docker**           | Containerized deployment |

---

## Technologies & Libraries

### 1. MCP (Model Context Protocol) ⭐ MOST IMPORTANT

**What it is:** A standard protocol for AI tools to communicate with external systems (like our memory server).

**Why it matters:** This is how Claude, Gemini, Cursor will talk to 0xMemory.

**Key Concepts:**

- **Transport:** How messages are sent (stdio, HTTP, WebSocket)
- **Tools:** Actions the AI can take (remember, recall, forget)
- **Resources:** Data the AI can read (brain.md, facts.md)
- **Prompts:** Pre-built instruction templates

**Learning Resources:**
| Resource | Link | Time |
|----------|------|------|
| MCP Official Docs | https://modelcontextprotocol.io/introduction | 1-2 hours |
| MCP Specification | https://spec.modelcontextprotocol.io | 2-3 hours |
| MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk | Explore |
| Example MCP Servers | https://github.com/modelcontextprotocol/servers | Explore |

**Hands-on Practice:**

```bash
# Install MCP SDK
pip install mcp

# Create a minimal MCP server
# See: https://modelcontextprotocol.io/quickstart/server
```

---

### 2. ChromaDB (Vector Database)

**What it is:** A local vector database for storing and searching embeddings.

**Why it matters:** This powers the semantic search (find memories by meaning, not just keywords).

**Key Concepts:**

- **Collections:** Groups of related documents
- **Embeddings:** Vector representations of text
- **Similarity Search:** Finding documents by cosine distance
- **Metadata Filtering:** Filter results by tags, dates, etc.

**Learning Resources:**
| Resource | Link | Time |
|----------|------|------|
| ChromaDB Docs | https://docs.trychroma.com/ | 1-2 hours |
| Getting Started | https://docs.trychroma.com/getting-started | 30 min |
| ChromaDB GitHub | https://github.com/chroma-core/chroma | Explore |

**Hands-on Practice:**

```python
# Install ChromaDB
pip install chromadb

# Basic usage
import chromadb

# Create a client (persistent storage)
client = chromadb.PersistentClient(path="./chroma_db")

# Create a collection
collection = client.create_collection("memories")

# Add documents
collection.add(
    documents=["The API uses JWT authentication"],
    ids=["fact-1"],
    metadatas=[{"type": "fact", "tags": ["api", "auth"]}]
)

# Search by meaning
results = collection.query(
    query_texts=["How does login work?"],
    n_results=5
)
print(results)
```

---

### 3. Sentence Transformers (Embeddings)

**What it is:** Library for generating text embeddings locally (no API needed).

**Why it matters:** Converts text into vectors for semantic search. Runs 100% offline.

**Key Concepts:**

- **Embeddings:** Dense vector representations (e.g., 384 dimensions)
- **Similarity:** Similar texts have similar embeddings
- **Models:** Different models have different quality/speed tradeoffs

**Recommended Models:**

| Model                   | Size  | Dimensions | Quality | Speed   |
| ----------------------- | ----- | ---------- | ------- | ------- |
| `all-MiniLM-L6-v2`      | 80MB  | 384        | Good    | Fast ⚡ |
| `all-mpnet-base-v2`     | 420MB | 768        | Better  | Medium  |
| `nomic-embed-text-v1.5` | 550MB | 768        | Best    | Slower  |

**Learning Resources:**
| Resource | Link | Time |
|----------|------|------|
| Official Docs | https://www.sbert.net/ | 1 hour |
| Pretrained Models | https://www.sbert.net/docs/pretrained_models.html | Browse |
| Usage Examples | https://www.sbert.net/docs/usage/semantic_textual_similarity.html | 30 min |

**Hands-on Practice:**

```python
# Install
pip install sentence-transformers

from sentence_transformers import SentenceTransformer

# Load model (downloads on first use)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings
texts = [
    "The API uses JWT authentication",
    "Login is handled by JWT tokens",
    "The database is PostgreSQL"
]

embeddings = model.encode(texts)
print(f"Shape: {embeddings.shape}")  # (3, 384)

# Calculate similarity
from sklearn.metrics.pairwise import cosine_similarity
similarity = cosine_similarity([embeddings[0]], [embeddings[1]])
print(f"Similarity: {similarity[0][0]:.2f}")  # ~0.85 (high)
```

---

### 4. Python Async Programming

**What it is:** Writing non-blocking code using `async`/`await`.

**Why it matters:** MCP server uses async for handling multiple requests.

**Key Concepts:**

- `async def` — Define async functions
- `await` — Wait for async operations
- `asyncio` — Python's async runtime

**Learning Resources:**
| Resource | Link | Time |
|----------|------|------|
| Real Python Guide | https://realpython.com/async-io-python/ | 1-2 hours |
| asyncio Docs | https://docs.python.org/3/library/asyncio.html | Reference |

**Hands-on Practice:**

```python
import asyncio

async def fetch_data():
    print("Fetching...")
    await asyncio.sleep(1)  # Simulate I/O
    return "Data received"

async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

---

### 5. Typer + Rich (CLI Framework)

**What it is:** Libraries for building beautiful command-line interfaces.

**Why it matters:** 0xMemory is terminal-first—the CLI needs to be excellent.

**Key Concepts:**

- **Typer:** Declarative CLI with type hints
- **Rich:** Beautiful terminal formatting, tables, progress bars

**Learning Resources:**
| Resource | Link | Time |
|----------|------|------|
| Typer Docs | https://typer.tiangolo.com/ | 1 hour |
| Rich Docs | https://rich.readthedocs.io/ | 1 hour |

**Hands-on Practice:**

```python
# Install
pip install typer rich

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def status():
    """Show brain status"""
    table = Table(title="🧠 0xMemory Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Facts", "42")
    table.add_row("Decisions", "7")
    table.add_row("Last Updated", "2 hours ago")
    console.print(table)

if __name__ == "__main__":
    app()
```

---

### 6. Pydantic (Data Validation)

**What it is:** Data validation using Python type hints.

**Why it matters:** Config files, memory entries, API responses all need validation.

**Learning Resources:**
| Resource | Link | Time |
|----------|------|------|
| Pydantic Docs | https://docs.pydantic.dev/ | 1 hour |
| Getting Started | https://docs.pydantic.dev/latest/concepts/models/ | 30 min |

**Hands-on Practice:**

```python
# Install
pip install pydantic pyyaml

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Memory(BaseModel):
    id: str
    content: str
    type: str  # fact, decision, learning
    tags: List[str] = []
    created_at: datetime = datetime.now()
    salience: float = 0.5

# Validate data
memory = Memory(
    id="fact-1",
    content="The API uses JWT",
    type="fact",
    tags=["api", "auth"]
)
print(memory.model_dump_json(indent=2))
```

---

### 7. LiteLLM (Optional: LLM Abstraction)

**What it is:** Unified API for calling OpenAI, Gemini, Claude, Ollama.

**Why it matters:** Knowledge extraction uses an LLM to identify facts/decisions.

**Learning Resources:**
| Resource | Link | Time |
|----------|------|------|
| LiteLLM Docs | https://docs.litellm.ai/ | 1 hour |
| Supported Providers | https://docs.litellm.ai/docs/providers | Browse |

**Hands-on Practice:**

```python
# Install
pip install litellm

from litellm import completion

# Works with any provider
response = completion(
    model="gemini/gemini-2.0-flash",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

---

## API Keys & Accounts

### Reality Check: Free Tier Limits (Jan 2026)

> ⚠️ **Important:** Free tiers have strict limits. Plan your development accordingly!

| Provider             | Model            | RPM | RPD    | Best Use       |
| -------------------- | ---------------- | --- | ------ | -------------- |
| **Google AI Studio** | gemini-2.5-flash | 5   | 20     | Demo only      |
| **Google AI Studio** | gemini-3-flash   | 5   | 20     | Demo only      |
| **Groq**             | llama-3.1-8b     | 30  | 14,400 | Development ⭐ |
| **Ollama (Colab)**   | llama3.2:3b      | ∞   | ∞      | Primary dev ⭐ |

### Development Strategy (Free Resources Only)

```
┌─────────────────────────────────────────────────────┐
│              DEVELOPMENT FLOW                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│   PRIMARY (Daily Coding)                             │
│   └── Ollama on Google Colab                        │
│       ├── llama3.2:3b (chat/extraction)             │
│       └── nomic-embed-text (embeddings)             │
│       └── Free GPU, unlimited requests              │
│                                                      │
│   FALLBACK (If Colab down)                          │
│   └── Groq Free Tier                                │
│       └── 14,400 req/day (very generous!)           │
│                                                      │
│   PRODUCTION/DEMO (Save these!)                      │
│   └── Gemini API                                    │
│       └── 40 req/day total (combine models)         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Required API Keys

| Service           | Purpose           | Free Limit       | Get Key                                |
| ----------------- | ----------------- | ---------------- | -------------------------------------- |
| **Groq** ⭐       | LLM fallback      | 14,400/day       | https://console.groq.com/keys          |
| **Google Gemini** | Production/demo   | 20/day per model | https://aistudio.google.com/app/apikey |
| **Ollama**        | Primary (no key!) | Unlimited        | Just install                           |

### Optional

| Service       | Purpose         | Notes             |
| ------------- | --------------- | ----------------- |
| **OpenAI**    | Alternative LLM | $5 credit expires |
| **Anthropic** | Claude API      | Limited free tier |
| **ngrok**     | Colab tunneling | Free tier works   |

### Setting Up API Keys

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc)

# Required
export GROQ_API_KEY="gsk_xxx..."        # Get from console.groq.com
export GEMINI_API_KEY="AIza..."         # Get from aistudio.google.com

# Optional (for Colab Ollama tunneling)
export NGROK_AUTH_TOKEN="xxx..."        # Get from ngrok.com

# For Ollama on Colab - set when running
export OLLAMA_HOST="https://xxx.ngrok.io"  # From Colab notebook
```

### LLM Priority Configuration

```yaml
# config.yaml - Use this order for free development
llm:
  providers:
    # Priority 1: Ollama on Colab (unlimited, free)
    - name: ollama
      host: "${OLLAMA_HOST}"
      model: llama3.2:3b

    # Priority 2: Groq (14,400/day free!)
    - name: groq
      model: llama-3.1-8b-instant

    # Priority 3: Gemini (save for demos, 20/day)
    - name: gemini
      model: gemini-3-flash

embeddings:
  # Always local - no API needed
  model: all-MiniLM-L6-v2
  # OR via Ollama:
  # model: nomic-embed-text
```

---

## Development Environment

### Required Software

| Software   | Version | Installation                           |
| ---------- | ------- | -------------------------------------- |
| **Python** | 3.11+   | `sudo apt install python3.11` or pyenv |
| **pip**    | Latest  | Comes with Python                      |
| **Git**    | Any     | `sudo apt install git`                 |
| **Ollama** | Latest  | https://ollama.ai/download             |

### Recommended Tools

| Tool               | Purpose                       | Link                                      |
| ------------------ | ----------------------------- | ----------------------------------------- |
| **VS Code**        | IDE with great Python support | https://code.visualstudio.com/            |
| **Claude Desktop** | Test MCP integration          | https://claude.ai/download                |
| **Gemini CLI**     | Test MCP integration          | `npm install -g @anthropic-ai/gemini-cli` |

### Project Setup

```bash
# Clone the repo
cd ~/Projects/0xMemory

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies (once we have them)
pip install -e ".[dev]"
```

---

## Learning Resources

### MCP Protocol (PRIORITY #1)

| Resource                | Type      | Time    | Link                                                                  |
| ----------------------- | --------- | ------- | --------------------------------------------------------------------- |
| MCP Introduction        | Docs      | 30 min  | https://modelcontextprotocol.io/introduction                          |
| Building MCP Servers    | Tutorial  | 1 hour  | https://modelcontextprotocol.io/quickstart/server                     |
| MCP Python SDK Examples | Code      | Explore | https://github.com/modelcontextprotocol/python-sdk/tree/main/examples |
| Official MCP Servers    | Reference | Browse  | https://github.com/modelcontextprotocol/servers                       |

### Vector Search & RAG

| Resource                     | Type     | Time      | Link                                                                        |
| ---------------------------- | -------- | --------- | --------------------------------------------------------------------------- |
| What are Embeddings?         | Video    | 15 min    | https://www.youtube.com/watch?v=viZrOnJclY0                                 |
| ChromaDB Tutorial            | Tutorial | 30 min    | https://docs.trychroma.com/getting-started                                  |
| RAG from Scratch (LangChain) | Video    | 1 hour    | https://www.youtube.com/watch?v=sVcwVQRHIc8                                 |
| Building RAG Applications    | Course   | 2-3 hours | https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag/ |

### Python Async

| Resource              | Type    | Time      | Link                                           |
| --------------------- | ------- | --------- | ---------------------------------------------- |
| Async IO in Python    | Article | 1 hour    | https://realpython.com/async-io-python/        |
| asyncio Official Docs | Docs    | Reference | https://docs.python.org/3/library/asyncio.html |

### CLI Development

| Resource       | Type | Time   | Link                                                    |
| -------------- | ---- | ------ | ------------------------------------------------------- |
| Typer Tutorial | Docs | 30 min | https://typer.tiangolo.com/tutorial/                    |
| Rich Library   | Docs | 30 min | https://rich.readthedocs.io/en/latest/introduction.html |

---

## Recommended Learning Path

### Week 1: Foundations

| Day         | Focus             | Activities                                             |
| ----------- | ----------------- | ------------------------------------------------------ |
| **Day 1-2** | MCP Protocol      | Read MCP docs, build hello-world MCP server            |
| **Day 3**   | Vector Embeddings | Understand embeddings, play with sentence-transformers |
| **Day 4**   | ChromaDB          | Set up ChromaDB, practice CRUD operations              |
| **Day 5**   | Python Async      | Review async/await, practice with asyncio              |
| **Day 6-7** | Integration       | Build a mini MCP server with ChromaDB backend          |

### Week 2: Specialization

| Day         | Focus               | Activities                       |
| ----------- | ------------------- | -------------------------------- |
| **Day 1-2** | CLI with Typer/Rich | Build beautiful CLI commands     |
| **Day 3**   | Pydantic            | Data models, config validation   |
| **Day 4**   | LiteLLM             | Test with Gemini/OpenAI/Ollama   |
| **Day 5-7** | Mini Project        | Build a simple memory MCP server |

---

## Checklist

### Before Starting Development

- [ ] **Python 3.11+ installed**
  - Verify: `python3 --version`
- [ ] **Virtual environment created**
  - `python3 -m venv .venv && source .venv/bin/activate`
- [ ] **Core libraries installed**
  - `pip install mcp chromadb sentence-transformers typer rich pydantic pyyaml`
- [ ] **At least one LLM API ready**
  - [ ] Gemini API key (recommended)
  - [ ] OR OpenAI API key
  - [ ] OR Ollama installed locally
- [ ] **MCP concepts understood**
  - [ ] What are Tools, Resources, Prompts?
  - [ ] How does stdio transport work?
  - [ ] Built a hello-world MCP server
- [ ] **Vector search concepts understood**
  - [ ] What are embeddings?
  - [ ] How does similarity search work?
  - [ ] Used ChromaDB for basic operations
- [ ] **Development tools ready**
  - [ ] Git configured
  - [ ] VS Code or preferred editor
  - [ ] Claude Desktop or Gemini CLI for testing

### Nice to Have

- [ ] Read OpenMemory source code for inspiration
- [ ] Explored existing MCP servers (filesystem, GitHub, etc.)
- [ ] Tested Ollama for fully offline operation
- [ ] Familiarized with project structure

---

## Quick Reference Commands

```bash
# Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install mcp chromadb sentence-transformers typer rich pydantic pyyaml litellm

# Run Ollama (local LLM)
ollama serve
ollama pull llama3
ollama pull nomic-embed-text

# Test embeddings
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('all-MiniLM-L6-v2'); print(m.encode(['hello']).shape)"

# Test ChromaDB
python -c "import chromadb; c = chromadb.Client(); print('ChromaDB OK')"

# Test MCP SDK
python -c "import mcp; print('MCP SDK OK')"
```

---

## Summary

### The 5 Things You MUST Understand

1. **MCP Protocol** — How AI tools will talk to your memory server
2. **Vector Embeddings** — How text becomes searchable by meaning
3. **ChromaDB** — Where embeddings are stored and searched
4. **Python Async** — How the server handles requests
5. **Dual Storage** — Markdown for humans, vectors for search

### Start Here

1. 📖 Read MCP Introduction: https://modelcontextprotocol.io/introduction
2. 🎥 Watch embeddings explainer: https://www.youtube.com/watch?v=viZrOnJclY0
3. 💻 Build hello-world MCP server with the Python SDK
4. 🧪 Experiment with ChromaDB + sentence-transformers

Once you've done these, you'll be ready to start Phase 1! 🚀

---

_Updated: 2026-01-09_
