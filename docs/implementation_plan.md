# 0xMemory Implementation Plan

> **Project:** 0xMemory - Terminal-First AI Agent with Persistent Memory  
> **Date:** 2026-01-09  
> **Vision:** End the Groundhog Effect - Build an AI that actually remembers

---

## Table of Contents

1. [Product Vision](#product-vision)
2. [Unique Differentiators](#unique-differentiators)
3. [Core Architecture](#core-architecture)
4. [Feature Specification](#feature-specification)
5. [Technical Stack](#technical-stack)
6. [Implementation Phases](#implementation-phases)
7. [Data Structures](#data-structures)
8. [Memory Algorithms](#memory-algorithms)
9. [Integration Points](#integration-points)
10. [Success Metrics](#success-metrics)

---

## Product Vision

### The Problem

Every AI coding assistant forgets you exist between sessions. You explain your project architecture, coding conventions, and preferences—then do it all over again next time.

### The Solution

**0xMemory** transforms your project folder into a **living brain**:

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR PROJECT                             │
│                                                             │
│   📁 .0xmemory/                                            │
│   ├── 🧠 brain.md        ← Human-editable context          │
│   ├── 📚 memory/         ← Learned facts & decisions       │
│   ├── 📄 documents/      ← Your docs for RAG               │
│   ├── 🗄️  vectordb/       ← Semantic search                 │
│   └── 📜 changelog.md    ← Session history                 │
│                                                             │
│   + Git versioned = Reproducible AI workflows              │
└─────────────────────────────────────────────────────────────┘
```

### One-Line Description

> A terminal-first AI agent that keeps persistent project state in human-editable Markdown, stores knowledge in a local vector DB, and enables reproducible, infinite-context workflows for solo developers.

---

## Unique Differentiators

### How 0xMemory is Different

| Aspect              | Competitors      | 0xMemory                         |
| ------------------- | ---------------- | -------------------------------- |
| **Interface**       | Cloud APIs, SDKs | Terminal CLI (ai_agent.py)       |
| **Memory Storage**  | Cloud databases  | Local vector DB + Markdown files |
| **Context Files**   | Hidden/binary    | Human-editable Markdown          |
| **Version Control** | None             | Git-native, every change tracked |
| **Scope**           | User-global      | Project-scoped (per repo brain)  |
| **Target User**     | Teams/Enterprise | Solo developers                  |
| **Learning**        | Automatic only   | Auto + human-editable            |
| **Offline**         | Usually no       | Fully offline capable            |
| **Reproducibility** | Limited          | Full audit trail in Git          |

### The 0xMemory Advantage

1. **Human-in-the-Loop Memory**

   - You can read, edit, and correct what the AI learns
   - No black-box memory systems

2. **Git-Native Workflows**

   - Every session logged, every decision tracked
   - Revert, branch, and collaborate on memory

3. **Project Brain, Not User Brain**

   - Each project has its own context
   - Switch projects, switch brains

4. **Terminal-First Design**

   - Built for developers who live in the terminal
   - No web UI required

5. **Offline Capable**
   - Local vector DB (ChromaDB)
   - Works with local LLMs (Ollama)

---

## Core Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         0xMemory                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────┐                                          │
│   │   ai_agent.py   │  ← CLI Entry Point                       │
│   │   (Python CLI)  │                                          │
│   └────────┬────────┘                                          │
│            │                                                    │
│   ┌────────▼──────────────────────────────────────────────┐    │
│   │              ORCHESTRATION LAYER                       │    │
│   │                                                        │    │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │    │
│   │  │ Context  │  │ Session  │  │    Action        │    │    │
│   │  │ Manager  │  │ Manager  │  │    Handler       │    │    │
│   │  └──────────┘  └──────────┘  └──────────────────┘    │    │
│   └────────┬──────────────────────────────────────────────┘    │
│            │                                                    │
│   ┌────────▼──────────────────────────────────────────────┐    │
│   │                 MEMORY LAYER                           │    │
│   │                                                        │    │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │    │
│   │  │ Markdown │  │ Vector   │  │  Knowledge       │    │    │
│   │  │ Context  │  │ Memory   │  │  Extractor       │    │    │
│   │  │ Files    │  │ (Chroma) │  │  (Facts/Decisions)│    │    │
│   │  └──────────┘  └──────────┘  └──────────────────┘    │    │
│   └────────┬──────────────────────────────────────────────┘    │
│            │                                                    │
│   ┌────────▼──────────────────────────────────────────────┐    │
│   │                   LLM LAYER                            │    │
│   │                                                        │    │
│   │  ┌────────────────────────────────────────────────┐   │    │
│   │  │  LiteLLM (Unified API)                         │   │    │
│   │  │  → Gemini | OpenAI | Claude | Ollama (local)   │   │    │
│   │  └────────────────────────────────────────────────┘   │    │
│   └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Session Start
     │
     ▼
┌─────────────────────┐
│ Load Context Files  │ ← brain.md, facts.md, preferences.md
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Build System Prompt │ ← Combine context + retrieved memories
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   User Message      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Retrieve Relevant   │ ← Semantic search in ChromaDB
│ Documents           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ LLM Reasoning       │ ← Generate response with full context
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Extract Knowledge   │ ← Identify facts, decisions, learnings
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Update Memory       │ ← Append to context files + vector DB
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Optional: Git Commit│ ← Track changes in version control
└─────────────────────┘
```

---

## Feature Specification

### Core Commands

| Command                   | Description                               |
| ------------------------- | ----------------------------------------- |
| `0xmemory init`           | Initialize a brain in the current project |
| `0xmemory chat`           | Start an interactive session              |
| `0xmemory status`         | Show brain statistics                     |
| `0xmemory ingest <path>`  | Add documents to the brain                |
| `0xmemory search <query>` | Search through memories                   |
| `0xmemory forget <id>`    | Remove a specific memory                  |
| `0xmemory export`         | Export brain for backup/sharing           |

### Memory Types

1. **Project Context** (`brain.md`)

   - High-level project description
   - Architecture overview
   - Key components
   - Human-maintained

2. **Facts** (`memory/facts.md`)

   - Discrete pieces of knowledge
   - Extracted from conversations
   - Auto-appended with timestamps

3. **Decisions** (`memory/decisions.md`)

   - Choices made with rationale
   - Links to relevant context
   - Useful for onboarding/handoff

4. **Learnings** (`memory/learnings.md`)

   - Gotchas, tips, lessons learned
   - Prevent repeating mistakes

5. **Preferences** (`memory/preferences.md`)

   - Coding style, communication style
   - Tool preferences
   - Human-editable

6. **Session Log** (`changelog.md`)
   - Append-only activity log
   - Git-friendly format

### RAG Capabilities

- **Semantic Search**: Find relevant docs by meaning
- **Hybrid Search**: Combine semantic + keyword
- **Context-Aware Retrieval**: Factor in current conversation
- **Source Attribution**: Know where information came from

---

## Technical Stack

### Core Technologies

| Component           | Technology            | Rationale                            |
| ------------------- | --------------------- | ------------------------------------ |
| **CLI Framework**   | Python + Typer        | Rich terminal UI, easy to use        |
| **Vector Database** | ChromaDB              | Local-first, lightweight, persistent |
| **Embeddings**      | sentence-transformers | Local, fast, no API needed           |
| **LLM Interface**   | LiteLLM               | Unified API for all providers        |
| **Configuration**   | YAML + Pydantic       | Human-readable, validated            |
| **Git Integration** | GitPython             | Automated commits                    |

### LLM Provider Support

| Provider      | Model             | Use Case                 |
| ------------- | ----------------- | ------------------------ |
| Google Gemini | gemini-2.0-flash  | Default, fast, free tier |
| OpenAI        | gpt-4o            | High quality             |
| Anthropic     | claude-3.5-sonnet | Great for code           |
| Ollama        | llama3, codellama | Fully offline            |

### Embedding Models

| Model             | Size  | Quality | Speed  |
| ----------------- | ----- | ------- | ------ |
| all-MiniLM-L6-v2  | 80MB  | Good    | Fast   |
| all-mpnet-base-v2 | 420MB | Better  | Medium |
| nomic-embed-text  | 550MB | Best    | Slower |

---

## Implementation Phases

### Phase 1: Foundation (MVP)

**Goal:** Working CLI with basic memory

**Deliverables:**

- [ ] CLI with init, chat, status commands
- [ ] Context file creation and loading
- [ ] Basic LLM integration (single provider)
- [ ] Git repository detection

**Timeline:** 1-2 weeks

---

### Phase 2: Memory Layer

**Goal:** Persistent semantic memory

**Deliverables:**

- [ ] ChromaDB integration
- [ ] Document ingestion pipeline
- [ ] Semantic search
- [ ] Embedding generation

**Timeline:** 1 week

---

### Phase 3: Intelligence

**Goal:** Retrieval-augmented generation

**Deliverables:**

- [ ] RAG pipeline
- [ ] Hybrid search (semantic + keyword)
- [ ] Context-aware prompting
- [ ] Multiple LLM providers

**Timeline:** 1 week

---

### Phase 4: Knowledge Extraction

**Goal:** Auto-learn from conversations

**Deliverables:**

- [ ] Fact extraction
- [ ] Decision logging
- [ ] Learning capture
- [ ] Memory consolidation

**Timeline:** 1 week

---

### Phase 5: Polish

**Goal:** Production-ready

**Deliverables:**

- [ ] Rich terminal UI
- [ ] Error handling
- [ ] Documentation
- [ ] Testing suite

**Timeline:** 1 week

---

### Phase 6: Advanced (Future)

**Optional Enhancements:**

- [ ] GraphRAG for relationships
- [ ] MCP server for integrations
- [ ] Web UI dashboard
- [ ] Team collaboration features

---

## Data Structures

### Directory Layout

```
project-root/
├── .0xmemory/
│   ├── config.yaml              # Configuration
│   ├── brain.md                 # Main context (human-edited)
│   ├── changelog.md             # Session history
│   ├── memory/
│   │   ├── facts.md             # Extracted facts
│   │   ├── decisions.md         # Decision log
│   │   ├── learnings.md         # Lessons learned
│   │   └── preferences.md       # User preferences
│   ├── documents/               # Source docs for RAG
│   │   ├── README.md
│   │   └── architecture.md
│   ├── sessions/
│   │   ├── current.md           # Active session
│   │   └── archive/             # Past sessions
│   └── vectordb/                # ChromaDB (gitignored)
│       └── chroma.sqlite3
└── ai_agent.py                  # Entry point
```

### Context File Format

```markdown
# 🧠 Project Brain

> This is the main context file for your project.
> Edit this to help 0xMemory understand your project.

## Project Overview

[Your project description here]

## Architecture

[Key components and how they fit together]

## Conventions

[Coding conventions, patterns, rules]

## Current Focus

[What you're currently working on]
```

### Memory Entry Format

```markdown
## [2026-01-09 12:30] `api` `authentication`

The project uses JWT tokens for authentication.
Tokens expire after 24 hours and refresh tokens last 30 days.

_Source: conversation about auth implementation_
```

---

## Memory Algorithms

### Knowledge Extraction

```
User Message + AI Response
         │
         ▼
┌─────────────────────┐
│ LLM Extraction      │
│ Prompt:             │
│ "Extract facts,     │
│  decisions, and     │
│  learnings from     │
│  this conversation" │
└──────────┬──────────┘
           │
           ▼
    ┌──────┴──────┐
    │             │
    ▼             ▼
  Facts       Decisions
    │             │
    ▼             ▼
facts.md    decisions.md
```

### Retrieval Strategy

```
User Query
    │
    ▼
┌─────────────────────┐
│ 1. Embed query      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Vector search    │ ← Top 10 by cosine similarity
│    (ChromaDB)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. Keyword boost    │ ← Re-rank by keyword overlap
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. Recency boost    │ ← Prefer recent memories
└──────────┬──────────┘
           │
           ▼
     Top 5 Results
```

### Memory Consolidation (Future)

Inspired by Shodh-Memory's approach:

```
Weekly Maintenance
       │
       ▼
┌─────────────────────┐
│ Summarize old facts │ ← Compress similar facts
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Remove duplicates   │ ← Dedup by semantic similarity
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Decay unused        │ ← A(t) = A₀ · e^(-λt)
└──────────┬──────────┘
           │
           ▼
   Optimized Memory
```

---

## Integration Points

### Git Integration

```python
# Auto-commit on session end
def end_session():
    # Append to changelog
    changelog.append(session_summary)

    # Stage changes
    repo.index.add([".0xmemory/"])

    # Commit with descriptive message
    repo.index.commit("[0xMemory] Session: Added 3 facts, 1 decision")
```

### MCP Server (Future)

```json
{
  "mcpServers": {
    "0xmemory": {
      "command": "0xmemory",
      "args": ["mcp-serve"],
      "tools": ["remember", "recall", "search_project", "update_fact"]
    }
  }
}
```

### LLM Provider Configuration

```yaml
# .0xmemory/config.yaml
llm:
  provider: gemini
  model: gemini-2.0-flash
  fallback:
    - provider: ollama
      model: llama3
```

---

## Success Metrics

### What Success Looks Like

| Metric                 | Target                                      |
| ---------------------- | ------------------------------------------- |
| **Context Recall**     | AI references past conversations accurately |
| **Session Continuity** | Pick up where you left off after days       |
| **Retrieval Latency**  | <500ms for memory search                    |
| **Setup Time**         | <2 minutes to first conversation            |
| **Zero Config**        | Works with sensible defaults                |

### User Experience Goals

1. **First Run**: `0xmemory init && 0xmemory chat` just works
2. **Day 2**: AI remembers yesterday's conversation
3. **Week 2**: AI knows your project deeply
4. **Month 2**: Irreplaceable development companion

---

## Open Questions

1. **Memory Limits**: How much memory before we need consolidation?
2. **Privacy**: How to handle sensitive information in memories?
3. **Collaboration**: How to share brains across team members?
4. **Updates**: How to handle conflicting facts?

---

## Next Steps

1. ✅ Research complete
2. ✅ Plan documented
3. ⏳ Implement MVP (Phase 1)
4. ⏳ Add memory layer (Phase 2)
5. ⏳ Build RAG pipeline (Phase 3)
6. ⏳ Knowledge extraction (Phase 4)
7. ⏳ Polish and release (Phase 5)

---

_This is a living document. Update as implementation progresses._
