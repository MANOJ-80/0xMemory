# 0xMemory Implementation Strategy

> **Version:** 1.0  
> **Date:** 2026-01-09  
> **Vision:** Cross-LLM, Infinite Context, Fully Local Memory Layer

---

## Executive Summary

**0xMemory** is a **local MCP (Model Context Protocol) server** that provides persistent, cross-LLM memory for AI agents. Unlike cloud-based solutions (Mem0, Zep) or SDK-focused tools (OpenMemory), 0xMemory is:

1. **Fully local** — No cloud, no third-party servers
2. **Cross-LLM compatible** — Works with Claude, Gemini, OpenAI via MCP
3. **Infinite context** — Overcomes token limits through smart retrieval
4. **Human-editable** — Markdown files you can read, edit, Git commit
5. **Project-scoped** — Per-repository brain, not user-global

---

## Table of Contents

1. [Product Vision](#product-vision)
2. [Unique Differentiators](#unique-differentiators)
3. [CLI Commands](#cli-commands)
4. [Memory Taxonomy](#memory-taxonomy)
5. [User Experience Goals](#user-experience-goals)
6. [Design Philosophy](#design-philosophy)
7. [System Architecture](#system-architecture)
8. [MCP Server Design](#mcp-server-design)
9. [Memory Architecture](#memory-architecture)
10. [Cross-LLM Strategy](#cross-llm-strategy)
11. [Infinite Context Strategy](#infinite-context-strategy)
12. [Technical Stack](#technical-stack)
13. [Implementation Phases](#implementation-phases)
14. [File & Data Structures](#file--data-structures)
15. [API Specification](#api-specification)
16. [Testing Strategy](#testing-strategy)
17. [Potential Limitations & Mitigations](#potential-limitations--how-to-overcome-them)
18. [Technology Justification](#technology-justification)
19. [Open Questions & Future](#open-questions--future-considerations)

---

## Product Vision

### The Problem

Every AI coding assistant forgets you exist between sessions. You explain your project architecture, coding conventions, and preferences—then do it all over again next time. This is the **"Groundhog Effect"**.

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
│   ├── 🗄️  .store/         ← Vector DB + SQLite              │
│   └── 📜 sessions/       ← Session history                 │
│                                                             │
│   + Git versioned = Reproducible AI workflows              │
└─────────────────────────────────────────────────────────────┘
```

### One-Line Description

> A terminal-first AI memory layer that keeps persistent project state in human-editable Markdown, stores knowledge in a local vector DB, and enables cross-LLM workflows for solo developers via MCP.

---

## Unique Differentiators

### How 0xMemory is Different

| Aspect              | Competitors      | 0xMemory                         |
| ------------------- | ---------------- | -------------------------------- |
| **Interface**       | Cloud APIs, SDKs | MCP Server (works with any LLM)  |
| **Memory Storage**  | Cloud databases  | Local vector DB + Markdown files |
| **Context Files**   | Hidden/binary    | Human-editable Markdown          |
| **Version Control** | None             | Git-native, every change tracked |
| **Scope**           | User-global      | Project-scoped (per repo brain)  |
| **Target User**     | Teams/Enterprise | Solo developers                  |
| **Learning**        | Automatic only   | Auto + human-editable            |
| **Offline**         | Usually no       | Fully offline capable            |
| **Reproducibility** | Limited          | Full audit trail in Git          |
| **LLM Lock-in**     | Single provider  | Cross-LLM via MCP                |

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

5. **Cross-LLM Compatibility**
   - Works with Claude, Gemini, OpenAI, Cursor
   - Switch LLMs, keep your memory

---

## CLI Commands

### Core Commands

| Command                   | Description                               |
| ------------------------- | ----------------------------------------- |
| `0xmemory init`           | Initialize a brain in the current project |
| `0xmemory serve`          | Start MCP server (for LLM clients)        |
| `0xmemory status`         | Show brain statistics                     |
| `0xmemory add <content>`  | Manually add a memory                     |
| `0xmemory search <query>` | Search through memories                   |
| `0xmemory ingest <path>`  | Add documents to the brain                |
| `0xmemory forget <id>`    | Remove a specific memory                  |
| `0xmemory export`         | Export brain for backup/sharing           |
| `0xmemory rebuild`        | Rebuild vector DB from Markdown           |

### Usage Examples

```bash
# Initialize a new brain in your project
cd my-project
0xmemory init

# Start MCP server for Claude/Gemini/Cursor
0xmemory serve

# Start MCP server on HTTP (for IDE integrations)
0xmemory serve --http --port 8080

# Check brain status
0xmemory status

# Add a fact manually
0xmemory add "The API uses port 3000" --type fact --tags api,config

# Search memories
0xmemory search "authentication"

# Ingest project documentation
0xmemory ingest ./docs/

# Export brain for backup
0xmemory export brain-backup.zip
```

---

## Memory Taxonomy

### Cognitive Framework

Based on research (ArXiv 2512.23343v1), 0xMemory organizes memory across two dimensions:

| Dimension  | Category         | Description                                  | 0xMemory File          |
| :--------- | :--------------- | :------------------------------------------- | :--------------------- |
| **Nature** | **Episodic**     | "How" - Events, sessions, tool actions       | `sessions/`, logs      |
|            | **Semantic**     | "What" - Facts, decisions, architecture      | `facts.md`, `brain.md` |
| **Scope**  | **Inside-trail** | Current session context (working memory)     | `sessions/current.md`  |
|            | **Cross-trail**  | Long-term state (persistent across sessions) | All memory files       |

### Core Memory Modules

1. **Project Brain** (`brain.md`)

   - **Type**: Semantic / Cross-trail (Core)
   - High-level project description, architecture, and "Source of Truth"
   - Human-maintained & AI-referenced

2. **Facts & Learnings** (`memory/facts.md`)

   - **Type**: Semantic / Cross-trail (Derived)
   - Discrete knowledge extracted from conversations
   - Prevent repeating "Gotchas" and reinforce correct patterns

3. **Decisions & Rationale** (`memory/decisions.md`)

   - **Type**: Episodic-to-Semantic / Cross-trail
   - Logs choices made with their context and reasoning
   - Facilitates onboarding and "Architecture Decision Records" (ADR)

4. **Session Archive** (`sessions/`)
   - **Type**: Episodic / Inside-trail → Cross-trail
   - Session summaries and activity logs
   - Compressed after session ends

### Context File Template (brain.md)

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

---

## User Experience Goals

### The Journey

| Milestone     | Experience                                   |
| ------------- | -------------------------------------------- |
| **First Run** | `0xmemory init && 0xmemory serve` just works |
| **Day 2**     | AI remembers yesterday's conversation        |
| **Week 2**    | AI knows your project deeply                 |
| **Month 2**   | Irreplaceable development companion          |

### Success Metrics

| Metric                 | Target                                      |
| ---------------------- | ------------------------------------------- |
| **Context Recall**     | AI references past conversations accurately |
| **Session Continuity** | Pick up where you left off after days       |
| **Retrieval Latency**  | < 500ms for memory search                   |
| **Setup Time**         | < 2 minutes to first memory                 |
| **Zero Config**        | Works with sensible defaults                |

---

## Design Philosophy

### Core Principles

| Principle           | Implementation                                              |
| ------------------- | ----------------------------------------------------------- |
| **Local-First**     | SQLite + ChromaDB, no external dependencies at runtime      |
| **Human-Readable**  | All memory stored as Markdown, viewable in any editor       |
| **Git-Native**      | Every change is tracked, revertible, branchable             |
| **LLM-Agnostic**    | MCP protocol means any compatible client works              |
| **Zero Lock-in**    | Your data is yours—plain files, standard formats            |
| **Offline-Capable** | Works with local embeddings (Ollama, sentence-transformers) |

### What We're NOT Building

- ❌ Cloud service / SaaS
- ❌ User-global memory (we're project-scoped)
- ❌ SDK for app developers (we're terminal-first)
- ❌ Complex knowledge graph (overkill for solo devs)
- ❌ Multi-tenant system

### Inspiration Sources

| Solution         | What We Take                             | What We Avoid                 |
| ---------------- | ---------------------------------------- | ----------------------------- |
| **Mem0**         | Extraction + Update pipeline             | Cloud dependency              |
| **OpenMemory**   | Multi-sector memory, decay engine        | Heavy infrastructure          |
| **Shodh-Memory** | Offline MCP server, single binary        | Limited LLM support           |
| **MARM**         | Cross-LLM memory via shared DB           | Complex setup                 |
| **Gemini CLI**   | Human-editable context files (GEMINI.md) | No persistent semantic memory |

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           YOUR DEVELOPMENT MACHINE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Claude      │  │  Gemini CLI  │  │  Cursor      │  │  Any MCP    │ │
│  │  Desktop     │  │              │  │  /Windsurf   │  │  Client     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                 │                 │                  │        │
│         └────────────────┬┴─────────────────┴──────────────────┘        │
│                          │ MCP Protocol (stdio/HTTP)                     │
│                          ▼                                               │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      0xMemory MCP Server                          │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  MCP Interface Layer                                        │  │  │
│  │  │  - Tool handlers (remember, recall, search, list, forget)   │  │  │
│  │  │  - Resource providers (brain.md, facts.md, etc.)            │  │  │
│  │  │  - Prompt templates                                         │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  Memory Engine                                              │  │  │
│  │  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │  │  │
│  │  │  │ Markdown    │  │ Vector Store │  │ Knowledge        │   │  │  │
│  │  │  │ Manager     │  │ (ChromaDB)   │  │ Extractor        │   │  │  │
│  │  │  └─────────────┘  └──────────────┘  └──────────────────┘   │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  Embedding Layer                                            │  │  │
│  │  │  - Local: sentence-transformers (all-MiniLM-L6-v2)         │  │  │
│  │  │  - Optional: OpenAI, Gemini, Ollama embeddings              │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                              │                                           │
│  ┌───────────────────────────▼───────────────────────────────────────┐  │
│  │                     Project Directory                              │  │
│  │  .0xmemory/                                                        │  │
│  │  ├── config.yaml          # Settings                               │  │
│  │  ├── brain.md             # Human-editable project context         │  │
│  │  ├── memory/                                                       │  │
│  │  │   ├── facts.md         # Extracted facts                        │  │
│  │  │   ├── decisions.md     # Decision log                           │  │
│  │  │   └── sessions/        # Session archives                       │  │
│  │  ├── documents/           # Source docs for RAG                    │  │
│  │  └── .store/              # ChromaDB + SQLite (gitignored)         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component               | Responsibility                                        |
| ----------------------- | ----------------------------------------------------- |
| **MCP Interface**       | Handles protocol, routes to tools, manages resources  |
| **Memory Engine**       | Orchestrates storage, retrieval, and updates          |
| **Markdown Manager**    | CRUD for human-readable `.md` files                   |
| **Vector Store**        | Semantic search via embeddings (ChromaDB)             |
| **Knowledge Extractor** | LLM-based fact/decision extraction from conversations |
| **Embedding Layer**     | Generates vector representations of text              |

### Data Flow

```
Session Start (LLM connects via MCP)
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
│   User Query        │ ← Via MCP tool call (recall, remember, etc.)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Retrieve Relevant   │ ← Semantic search in ChromaDB
│ Memories            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Return to LLM       │ ← Formatted context for the AI
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Store New Memory    │ ← If remember tool is called
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Update Markdown +   │ ← Write to facts.md + ChromaDB
│ Vector DB           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Optional: Git Commit│ ← Auto-commit if configured
└─────────────────────┘
```

### Memory Algorithms

#### Knowledge Extraction Flow

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
    │             │
    └──────┬──────┘
           ▼
      ChromaDB
    (embeddings)
```

#### Retrieval Strategy

```
User Query (via recall tool)
    │
    ▼
┌─────────────────────┐
│ 1. Embed query      │ ← sentence-transformers
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
┌─────────────────────┐
│ 5. Salience boost   │ ← Prefer high-importance memories
└──────────┬──────────┘
           │
           ▼
     Top 5 Results
```

#### Memory Consolidation (Maintenance)

Inspired by Shodh-Memory's approach:

```
Weekly/Monthly Maintenance
       │
       ▼
┌─────────────────────┐
│ Summarize old facts │ ← Compress similar facts
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Remove duplicates   │ ← Dedup by semantic similarity > 0.95
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Decay unused        │ ← A(t) = A₀ · e^(-λt)
│ (reduce salience)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Archive old sessions│ ← Move to archive/ after 90 days
└──────────┬──────────┘
           │
           ▼
   Optimized Memory
```

### Git Integration

Auto-commit session changes:

```python
# Auto-commit on session end
def end_session():
    # Generate session summary
    summary = summarize_session(current_session)

    # Write to session archive
    archive_session(current_session, summary)

    # Stage memory changes
    repo.index.add([".0xmemory/memory/", ".0xmemory/sessions/"])

    # Commit with descriptive message
    facts_added = count_new_facts()
    decisions_added = count_new_decisions()

    repo.index.commit(
        f"[0xMemory] Session: +{facts_added} facts, +{decisions_added} decisions"
    )
```

---

## MCP Server Design

### Why MCP?

MCP (Model Context Protocol) is the **universal connector** for AI tools:

- **Claude Desktop/Code** — Native MCP support
- **Cursor, Windsurf** — MCP via `.mcp.json` config
- **Gemini CLI** — MCP support built-in
- **Any future tool** — Open standard, JSON-RPC 2.0

By building 0xMemory as an MCP server, we get **cross-LLM compatibility for free**.

### Transport Options

| Transport     | Use Case                                  | Implementation |
| ------------- | ----------------------------------------- | -------------- |
| **stdio**     | Local CLI tools (Claude Code, Gemini CLI) | Primary mode   |
| **HTTP**      | IDE integrations (Cursor, Windsurf)       | Optional mode  |
| **WebSocket** | Future extensions                         | Not in v1      |

### MCP Tools (Actions the AI Can Take)

```yaml
tools:
  - name: remember
    description: Store a new memory (fact, decision, learning)
    parameters:
      content: string # The memory content
      type: enum # fact | decision | learning | preference
      tags: string[] # Optional categorization tags
      source: string # Where this came from (optional)
    returns:
      id: string # Memory ID for future reference

  - name: recall
    description: Search memories semantically by meaning
    parameters:
      query: string # Natural language query
      limit: integer # Max results (default: 5)
      types: string[] # Filter by memory type
    returns:
      memories: Memory[] # Matching memories with scores

  - name: list
    description: List all memories, optionally filtered
    parameters:
      type: string # Filter by type (optional)
      since: datetime # Filter by date (optional)
      limit: integer # Max results (default: 20)
    returns:
      memories: Memory[]

  - name: forget
    description: Remove a memory by ID
    parameters:
      id: string # Memory ID to remove
    returns:
      success: boolean

  - name: update
    description: Update an existing memory
    parameters:
      id: string # Memory ID
      content: string # New content
    returns:
      success: boolean

  - name: reinforce
    description: Strengthen a memory (increases recall priority)
    parameters:
      id: string # Memory ID
    returns:
      new_salience: float
```

### MCP Resources (Files the AI Can Read)

```yaml
resources:
  - uri: brain://context
    name: Project Context
    description: Main project brain (brain.md)
    mimeType: text/markdown

  - uri: brain://facts
    name: Known Facts
    description: All extracted facts
    mimeType: text/markdown

  - uri: brain://decisions
    name: Decision Log
    description: Past decisions and rationale
    mimeType: text/markdown

  - uri: brain://session/current
    name: Current Session
    description: Ongoing conversation context
    mimeType: text/markdown
```

### MCP Prompts (Pre-built Instructions)

```yaml
prompts:
  - name: project_context
    description: Get full project context for any task
    template: |
      You are working on a project with the following context:

      ## Project Brain
      {brain_content}

      ## Recent Facts
      {recent_facts}

      ## Relevant Decisions
      {relevant_decisions}

  - name: extract_knowledge
    description: Extract learnings from a conversation
    template: |
      Review this conversation and extract:
      1. New facts about the project
      2. Decisions made with rationale
      3. Lessons learned or gotchas

      Conversation:
      {conversation}
```

---

## Memory Architecture

### Memory Types (Sectors)

Based on research (OpenMemory, Mem0, Google Context Engineering):

| Sector         | Description                | Storage             | Example                                  |
| -------------- | -------------------------- | ------------------- | ---------------------------------------- |
| **Semantic**   | Facts, definitions, rules  | `facts.md` + vector | "API uses JWT auth with 24h expiry"      |
| **Episodic**   | Events, sessions, actions  | `sessions/`         | "Debugged auth issue on 2026-01-09"      |
| **Procedural** | How-to knowledge, patterns | `patterns.md`       | "Always run tests before commit"         |
| **Decisions**  | Choices + rationale        | `decisions.md`      | "Chose Postgres over MongoDB because..." |

### Memory Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MEMORY LIFECYCLE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. ACQUISITION                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Conversation → Extract facts/decisions → Validate → Store   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│  2. STORAGE (Dual)          ▼                                        │
│  ┌────────────────────┐  ┌────────────────────┐                     │
│  │ Markdown Files     │  │ Vector Database    │                     │
│  │ (Human-readable)   │  │ (Semantic search)  │                     │
│  │ → facts.md         │  │ → ChromaDB         │                     │
│  │ → decisions.md     │  │ → SQLite backend   │                     │
│  └────────────────────┘  └────────────────────┘                     │
│                              │                                       │
│  3. RETRIEVAL               ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Query → Embed → Vector Search → Re-rank → Top-K results     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│  4. MAINTENANCE             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Decay unused → Consolidate similar → Deduplicate → Archive  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Dual Storage Strategy

**Why both Markdown AND Vector DB?**

| Aspect          | Markdown Files                  | Vector Database       |
| --------------- | ------------------------------- | --------------------- |
| **Purpose**     | Human readability, Git tracking | Fast semantic search  |
| **Access**      | Direct file editing             | API queries           |
| **Versioning**  | Git-native                      | Rebuild from Markdown |
| **Portability** | Copy folder anywhere            | Tied to runtime       |
| **Debugging**   | Open in any editor              | Need CLI tools        |

**Sync Strategy:**

- Markdown is **source of truth**
- Vector DB is **derived index** (can be rebuilt)
- On startup: Verify sync, rebuild if needed
- On change: Update both atomically

### Memory Entry Schema

```yaml
Memory:
  id: string # UUID
  content: string # The actual memory text
  type: enum # semantic | episodic | procedural | decision
  created_at: datetime
  updated_at: datetime
  accessed_at: datetime # For decay calculations
  salience: float # 0.0-1.0, importance score
  tags: string[] # Categorization
  source: string # Origin (conversation, manual, import)
  embedding: float[] # Vector representation (stored in ChromaDB)
  metadata:
    session_id: string # Which session created this
    related_to: string[] # Links to other memory IDs
```

---

## Cross-LLM Strategy

### The Challenge

Each AI tool (Claude, Gemini, Cursor) has its own session. How do we share memory across all of them?

### The Solution: MCP as Universal Bridge

```
┌─────────────────────────────────────────────────────────────────┐
│                    CROSS-LLM MEMORY SHARING                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Claude Code        Gemini CLI         Cursor                  │
│       │                  │                 │                     │
│       │    MCP           │    MCP          │    MCP              │
│       └──────────────────┼─────────────────┘                     │
│                          │                                       │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │  0xMemory MCP Server  │                          │
│              │  (Single Instance)    │                          │
│              └───────────┬───────────┘                          │
│                          │                                       │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │  Shared Memory Store  │                          │
│              │  .0xmemory/           │                          │
│              └───────────────────────┘                          │
│                                                                  │
│   Result: Switch from Claude to Gemini = Same memories!         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration for Each Client

**Claude Desktop/Code:**

```json
{
  "mcpServers": {
    "0xmemory": {
      "command": "0xmemory",
      "args": ["serve"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

**Gemini CLI:**

```bash
gemini mcp add 0xmemory -- 0xmemory serve
```

**Cursor/Windsurf (.mcp.json):**

```json
{
  "mcpServers": {
    "0xmemory": {
      "command": "0xmemory",
      "args": ["serve"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

---

## Infinite Context Strategy

### The Problem

Even 1M token context windows can't hold:

- Entire codebase
- All past conversations
- Full documentation

### The Solution: Smart Retrieval + Compression

```
┌─────────────────────────────────────────────────────────────────┐
│                   INFINITE CONTEXT STRATEGY                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LAYER 1: IMMEDIATE CONTEXT (Always Loaded)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • brain.md (project overview) - ~500 tokens              │  │
│  │  • Current task context - ~200 tokens                     │  │
│  │  • User preferences - ~100 tokens                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  LAYER 2: RETRIEVED CONTEXT (On-Demand)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Vector search results (top 5 relevant) - ~1000 tokens  │  │
│  │  • Related decisions - ~500 tokens                        │  │
│  │  • Recent session summary - ~300 tokens                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  LAYER 3: DEEP ARCHIVE (Searchable, Not Loaded)                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • All past facts                                         │  │
│  │  • All session transcripts                                │  │
│  │  • Ingested documents                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  TOTAL ACTIVE CONTEXT: ~2,600 tokens (fits ANY model!)          │
│  SEARCHABLE CONTEXT: Unlimited                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Retrieval Pipeline

```python
def retrieve_context(query: str, session_context: str) -> str:
    """
    Multi-stage retrieval for optimal context assembly.
    """

    # 1. Always include core brain context
    brain = load_file("brain.md")

    # 2. Semantic search for relevant memories
    query_embedding = embed(query)
    relevant_memories = vector_store.search(
        query_embedding,
        limit=5,
        filters={"salience": {"$gte": 0.3}}
    )

    # 3. Keyword boost for exact matches
    keyword_matches = keyword_search(query, top_k=3)

    # 4. Merge and re-rank
    all_results = merge_and_rerank(
        relevant_memories,
        keyword_matches,
        recency_weight=0.2,
        salience_weight=0.3,
        similarity_weight=0.5
    )

    # 5. Assemble context within token budget
    context = assemble_context(
        brain=brain,
        memories=all_results[:5],
        max_tokens=2500
    )

    return context
```

### Session Compression (Memory Folding)

When conversations get long, compress them:

```python
def fold_session(session_transcript: str) -> str:
    """
    Compress long sessions into summaries.
    Inspired by Manus AI's "Memory Folding" technique.
    """

    # If session is short, keep as-is
    if count_tokens(session_transcript) < 2000:
        return session_transcript

    # LLM-driven summarization
    summary = llm.summarize(
        content=session_transcript,
        instruction="""
        Compress this session into:
        1. Key decisions made
        2. Important facts learned
        3. Current task state
        4. Open questions

        Keep under 500 tokens.
        """
    )

    # Extract and persist facts/decisions
    extract_and_store_knowledge(session_transcript)

    return summary
```

### Why This Works: Detailed Explanation

> **Key Insight:** "Infinite context" does NOT mean stuffing everything into the LLM's context window.  
> It means **storing everything** but only **retrieving what's relevant**.

#### ❌ The Naive Approach (What We're NOT Doing)

```
"Infinite context" = Stuff EVERYTHING into context window
                   = 100K+ tokens every request
                   = Slow, expensive, CONTEXT ROT!

┌─────────────────────────────────────────────────────┐
│  CONTEXT WINDOW (e.g., 128K tokens)                 │
│  ┌───────────────────────────────────────────────┐  │
│  │ brain.md          (5K tokens)                 │  │
│  │ ALL facts         (20K tokens)                │  │
│  │ ALL decisions     (10K tokens)                │  │
│  │ ALL sessions      (50K tokens)                │  │
│  │ ALL documents     (40K tokens)                │  │
│  │ Current message   (500 tokens)                │  │
│  └───────────────────────────────────────────────┘  │
│  TOTAL: 125K tokens 💸💸💸 (expensive + slow)       │
└─────────────────────────────────────────────────────┘
```

**Problems with this approach:**

1. **Cost:** More tokens = more money (API pricing is per token)
2. **Latency:** More tokens = slower responses (linear increase)
3. **Context Rot:** Performance DEGRADES with more tokens (proven by Chroma research)
4. **"Lost in the Middle":** LLMs ignore information in the middle of long contexts

#### ✅ Our Approach: Smart Retrieval

```
"Infinite context" = STORE everything, RETRIEVE only what's relevant
                   = ~2-3K tokens per request (always!)
                   = Fast, cheap, accurate

┌─────────────────────────────────────────────────────┐
│  CONTEXT WINDOW                                      │
│  ┌───────────────────────────────────────────────┐  │
│  │ brain.md summary      (500 tokens)  ← Always  │  │
│  │ TOP 5 relevant facts  (800 tokens)  ← Smart   │  │
│  │ Related decisions     (400 tokens)  ← Smart   │  │
│  │ Session summary       (300 tokens)  ← Compressed│ │
│  │ Current message       (500 tokens)            │  │
│  └───────────────────────────────────────────────┘  │
│  TOTAL: ~2,500 tokens ✨ (cheap + fast)             │
└─────────────────────────────────────────────────────┘

                        ↑ Only the RELEVANT stuff!

┌─────────────────────────────────────────────────────┐
│  STORAGE (ChromaDB + Markdown)                      │
│  ┌───────────────────────────────────────────────┐  │
│  │ 1000+ facts        (searchable by meaning)    │  │
│  │ 100+ decisions     (searchable by meaning)    │  │
│  │ Years of sessions  (archived, searchable)     │  │
│  │ All documents      (indexed, searchable)      │  │
│  └───────────────────────────────────────────────┘  │
│  UNLIMITED STORAGE ♾️ (not in context window!)      │
└─────────────────────────────────────────────────────┘
```

#### Step-by-Step: How It Works

**Step 1: User Asks a Question**

```
User: "How does our authentication work?"
```

**Step 2: We Search Our Memory (NOT in LLM context yet)**

```python
# Embed the question
query_embedding = embed("How does our authentication work?")

# Search ChromaDB (milliseconds, not tokens!)
relevant_memories = chroma.query(
    query_embedding,
    n_results=5,  # Only top 5!
    where={"type": {"$in": ["fact", "decision"]}}
)

# Results:
# 1. "The API uses JWT tokens for auth" (0.92 similarity)
# 2. "Tokens expire after 24 hours" (0.87 similarity)
# 3. "Refresh tokens last 30 days" (0.85 similarity)
# 4. "Auth middleware is in auth.py" (0.82 similarity)
# 5. "We chose JWT over session cookies" (0.78 similarity)
```

**Step 3: Build Minimal Context**

```python
context = f"""
## Project Context
{brain_summary}  # ~500 tokens

## Relevant Knowledge
- The API uses JWT tokens for authentication
- Tokens expire after 24 hours, refresh after 30 days
- Auth middleware is in auth.py
- We chose JWT over session cookies because...

## Current Session
{session_summary}  # ~300 tokens

## User Question
How does our authentication work?
"""

# Total: ~2,500 tokens (fits ANY model!)
```

**Step 4: Send to LLM**

The LLM only sees the **relevant** 2,500 tokens, not all 100K+ of stored knowledge!

#### Semantic Search: Finding by Meaning

This is the magic that makes it work:

```python
# Question: "How does login work?"
# This finds: "JWT authentication is used for user sessions"
# Even though "login" ≠ "JWT" literally!

# The magic: Embeddings know they're semantically similar
embed("How does login work?") ≈ embed("JWT authentication")
```

Vector embeddings capture the **meaning** of text, not just keywords. So:

- "login" → finds "authentication"
- "password storage" → finds "hashing", "bcrypt"
- "API security" → finds "JWT", "auth middleware"

#### Recency + Relevance Scoring

We don't just use similarity—we combine multiple factors:

```python
def score_memory(memory, query):
    # Semantic similarity (0-1)
    similarity = cosine_similarity(embed(query), memory.embedding)

    # Recency boost (recent = higher)
    days_old = (now - memory.created_at).days
    recency = 1.0 / (1 + days_old * 0.1)

    # Salience (how important is this memory)
    salience = memory.salience

    # Combined score
    return (similarity * 0.5) + (recency * 0.2) + (salience * 0.3)
```

#### Token Budget Breakdown

```
┌─────────────────────────────────────────────────────┐
│  TOKEN BUDGET PER REQUEST                           │
├─────────────────────────────────────────────────────┤
│                                                      │
│  System Prompt:                                      │
│  ├── Brain summary:         500 tokens              │
│  ├── User preferences:      100 tokens              │
│  └── Instructions:          200 tokens              │
│                             ─────────               │
│                              800 tokens             │
│                                                      │
│  Retrieved Context:                                  │
│  ├── Top 5 facts:           800 tokens              │
│  ├── Related decisions:     400 tokens              │
│  └── Session summary:       300 tokens              │
│                             ─────────               │
│                             1,500 tokens            │
│                                                      │
│  User Message:               500 tokens             │
│                                                      │
│  ─────────────────────────────────────              │
│  TOTAL:                    2,800 tokens             │
│  ─────────────────────────────────────              │
│                                                      │
│  Works on: GPT-3.5 (4K), Claude (8K), Gemini (1M) ✅│
│                                                      │
└─────────────────────────────────────────────────────┘
```

#### Comparison: Approaches

| Approach             | Tokens/Request | Speed   | Cost    | Accuracy          |
| -------------------- | -------------- | ------- | ------- | ----------------- |
| **Stuff everything** | 100K+          | Slow 🐌 | High 💸 | Low (context rot) |
| **Our approach**     | 2-3K           | Fast ⚡ | Low 💰  | High (focused)    |

#### Summary: What "Infinite Context" Really Means

| Term                    | What It Means                                |
| ----------------------- | -------------------------------------------- |
| **Infinite STORAGE**    | Everything saved in ChromaDB + Markdown      |
| **Finite CONTEXT**      | Only relevant items loaded (2-3K tokens)     |
| **Smart RETRIEVAL**     | Search by meaning, not brute force           |
| **Session Compression** | Long conversations → short summaries         |
| **Works Everywhere**    | Same approach fits 4K, 8K, 128K, 1M contexts |

This is exactly what Mem0, OpenMemory, and all successful memory systems do. We're just doing it **locally** with **MCP**!

---

## Technical Stack

### Core Dependencies

| Component      | Library                 | Version | Rationale                      |
| -------------- | ----------------------- | ------- | ------------------------------ |
| **Language**   | Python                  | 3.11+   | Ecosystem, LLM libraries       |
| **MCP SDK**    | `mcp`                   | latest  | Official MCP implementation    |
| **Vector DB**  | `chromadb`              | 0.5+    | Local, lightweight, persistent |
| **Embeddings** | `sentence-transformers` | 3.0+    | Local, no API needed           |
| **CLI**        | `typer` + `rich`        | latest  | Beautiful terminal UI          |
| **Config**     | `pydantic` + `pyyaml`   | latest  | Validated configuration        |
| **Git**        | `gitpython`             | latest  | Automated commits              |

### Optional Dependencies

| Component       | Library   | Use Case                          |
| --------------- | --------- | --------------------------------- |
| **LLM API**     | `litellm` | External LLM calls for extraction |
| **HTTP Server** | `fastapi` | HTTP transport mode               |
| **Local LLM**   | `ollama`  | Fully offline operation           |

### Embedding Model Options

| Model                    | Size  | Quality   | Offline |
| ------------------------ | ----- | --------- | ------- |
| `all-MiniLM-L6-v2`       | 80MB  | Good      | ✅      |
| `all-mpnet-base-v2`      | 420MB | Better    | ✅      |
| `nomic-embed-text`       | 550MB | Best      | ✅      |
| `text-embedding-3-small` | API   | Excellent | ❌      |
| `gemini-embedding-001`   | API   | Excellent | ❌      |

**Default:** `all-MiniLM-L6-v2` (good balance of quality and size)

---

## Implementation Phases

### Phase 1: MCP Server Foundation (Week 1-2)

**Goal:** Working MCP server with basic memory operations

**Deliverables:**

- [ ] Project structure and packaging
- [ ] MCP server with stdio transport
- [ ] Core tools: `remember`, `recall`, `list`, `forget`
- [ ] Markdown file manager (brain.md, facts.md)
- [ ] Basic configuration (config.yaml)
- [ ] CLI commands: `init`, `serve`, `status`

**Verification:**

- Manual test with Claude Desktop
- Unit tests for memory operations

---

### Phase 2: Vector Search & Embeddings (Week 2-3)

**Goal:** Semantic search capabilities

**Deliverables:**

- [ ] ChromaDB integration
- [ ] Local embedding generation (sentence-transformers)
- [ ] Semantic search in `recall` tool
- [ ] Hybrid search (semantic + keyword)
- [ ] Document ingestion pipeline

**Verification:**

- Retrieval accuracy tests
- Latency benchmarks (<500ms target)

---

### Phase 3: Knowledge Extraction (Week 3-4)

**Goal:** Auto-learn from conversations

**Deliverables:**

- [ ] LLM-based fact extraction
- [ ] Decision logging with rationale
- [ ] Memory type classification
- [ ] Duplicate detection
- [ ] Conflict resolution

**Verification:**

- Extraction quality tests
- False positive rate measurement

---

### Phase 4: Cross-LLM & Polish (Week 4-5)

**Goal:** Production-ready, works with all major LLMs

**Deliverables:**

- [ ] HTTP transport mode (for Cursor/Windsurf)
- [ ] Configuration for all major clients
- [ ] Session management
- [ ] Memory decay & consolidation
- [ ] Rich CLI UI
- [ ] Documentation

**Verification:**

- End-to-end tests with Claude, Gemini, Cursor
- User acceptance testing

---

### Phase 5: Advanced Features (Future)

**Optional Enhancements:**

- [ ] GraphRAG for relationship tracking
- [ ] Temporal queries ("What was true last week?")
- [ ] Team collaboration (shared brains)
- [ ] Web dashboard
- [ ] VS Code extension

---

## File & Data Structures

### Directory Layout

```
project-root/
├── .0xmemory/
│   ├── config.yaml                # Configuration
│   ├── brain.md                   # Main project context (human-edited)
│   ├── memory/
│   │   ├── facts.md               # Extracted facts
│   │   ├── decisions.md           # Decision log with rationale
│   │   ├── patterns.md            # Procedural knowledge
│   │   └── preferences.md         # User/project preferences
│   ├── sessions/
│   │   ├── current.md             # Active session
│   │   └── archive/               # Past session summaries
│   │       └── 2026-01-09.md
│   ├── documents/                 # Source docs for RAG
│   │   └── (user-provided files)
│   └── .store/                    # Internal storage (gitignored)
│       ├── chroma/                # Vector database
│       ├── index.sqlite           # Metadata index
│       └── cache/                 # Embedding cache
└── .gitignore                     # Includes .0xmemory/.store/
```

### Config File (config.yaml)

```yaml
# 0xMemory Configuration
version: "1.0"

# Project identity
project:
  name: "My Project"
  description: "Optional project description"

# Embedding settings
embeddings:
  model: "all-MiniLM-L6-v2" # Local model
  # model: "text-embedding-3-small"  # or OpenAI
  # api_key_env: "OPENAI_API_KEY"

# LLM for knowledge extraction (optional)
llm:
  provider: "gemini"
  model: "gemini-2.0-flash"
  # api_key_env: "GEMINI_API_KEY"
  fallback:
    - provider: "ollama"
      model: "llama3"

# Memory settings
memory:
  max_facts: 1000
  decay_enabled: true
  decay_rate: 0.01 # Per day
  consolidation_interval: "weekly"

# Git integration
git:
  auto_commit: true
  commit_prefix: "[0xMemory]"
```

### Memory Entry Format (facts.md)

```markdown
# 📚 Facts & Knowledge

> Auto-extracted facts about the project. Feel free to edit!

---

## [2026-01-09 12:30] `api` `authentication`

The project uses JWT tokens for authentication. Access tokens expire after
24 hours, refresh tokens after 30 days.

_Source: conversation about auth implementation_
_ID: fact-a1b2c3d4_

---

## [2026-01-09 14:15] `database` `postgresql`

PostgreSQL is the main database. Using pg_vector extension for embeddings
storage alongside application data.

_Source: architecture discussion_
_ID: fact-e5f6g7h8_
```

### Decision Log Format (decisions.md)

```markdown
# 🎯 Decisions & Rationale

> Important decisions with their context and reasoning.

---

## [2026-01-09] Chose PostgreSQL over MongoDB

**Decision:** Use PostgreSQL as the primary database

**Context:** Needed a database for the new API service

**Alternatives Considered:**

- MongoDB: Good for unstructured data, but we have relational needs
- SQLite: Too limited for production multi-user scenario

**Rationale:**

- Strong ACID compliance
- pg_vector for embeddings
- Team familiarity
- Better querying for relational data

**Consequences:**

- Need to manage schema migrations
- Higher operational complexity than SQLite

_ID: decision-x1y2z3_
```

---

## API Specification

### Python API (for extensions)

```python
from oxmemory import Memory, MemoryType

# Initialize
mem = Memory(project_dir="/path/to/project")

# Store a fact
mem.remember(
    content="The API uses JWT authentication",
    type=MemoryType.SEMANTIC,
    tags=["api", "auth"],
    source="manual"
)

# Search memories
results = mem.recall(
    query="How does authentication work?",
    limit=5
)

# List all facts
facts = mem.list(type=MemoryType.SEMANTIC)

# Forget a memory
mem.forget(id="fact-a1b2c3d4")
```

### CLI Commands

```bash
# Initialize a new brain
0xmemory init

# Start MCP server (stdio mode)
0xmemory serve

# Start MCP server (HTTP mode for IDE integrations)
0xmemory serve --http --port 8080

# Show brain status
0xmemory status

# Manually add a memory
0xmemory add "The API uses port 3000" --type fact --tags api,config

# Search memories
0xmemory search "authentication"

# Ingest documents
0xmemory ingest ./docs/

# Export brain for backup
0xmemory export brain-backup.zip

# Rebuild vector index from markdown
0xmemory rebuild
```

---

## Testing Strategy

### Unit Tests

| Component        | Test Coverage                        |
| ---------------- | ------------------------------------ |
| Markdown Manager | CRUD operations, parsing, formatting |
| Vector Store     | Add, search, delete, filters         |
| Memory Engine    | Lifecycle, deduplication, decay      |
| MCP Interface    | Tool handlers, resource providers    |
| Embedding Layer  | Model loading, encoding, caching     |

### Integration Tests

| Scenario      | Description                                    |
| ------------- | ---------------------------------------------- |
| Full flow     | Init → Add memory → Search → Retrieve → Delete |
| Sync check    | Markdown ↔ Vector consistency                  |
| Rebuild       | Wipe vector DB, rebuild from Markdown          |
| Cross-session | Memory persists across server restarts         |

### End-to-End Tests

| Client         | Test                          |
| -------------- | ----------------------------- |
| Claude Desktop | Configure MCP, test all tools |
| Gemini CLI     | Add via MCP, verify recall    |
| Cursor         | HTTP mode, tool invocation    |

### Manual Acceptance Tests

1. **Day 1 Test:**

   - Init project
   - Have conversation about project architecture
   - Verify facts are extracted

2. **Day 2 Test:**

   - Start new session
   - Ask about yesterday's discussion
   - Verify memories are recalled correctly

3. **Cross-LLM Test:**
   - Add memory via Claude
   - Recall via Gemini
   - Verify same information available

---

## Success Criteria

| Metric                 | Target                              |
| ---------------------- | ----------------------------------- |
| **Retrieval Latency**  | < 500ms for search                  |
| **Accuracy**           | > 85% relevant results in top 5     |
| **Setup Time**         | < 2 minutes to first memory         |
| **Context Efficiency** | < 3000 tokens for full context      |
| **Offline Operation**  | 100% functionality without internet |
| **Cross-LLM**          | Works with Claude, Gemini, Cursor   |

---

## Potential Limitations & How to Overcome Them

### 1. Embedding Quality Issues

**The Problem:**

- Local embedding models (80-550MB) are less accurate than cloud APIs (OpenAI, Gemini)
- Semantic search may miss relevant memories or return irrelevant ones
- Domain-specific terminology may not be well-represented

**Mitigation Strategies:**

| Strategy           | Implementation                                    |
| ------------------ | ------------------------------------------------- |
| **Hybrid Search**  | Combine semantic (vector) + keyword (BM25) search |
| **Model Swapping** | Allow users to configure better models if needed  |
| **Reranking**      | Use LLM to rerank top-20 results to top-5         |
| **Fine-tuning**    | Future: Fine-tune embeddings on user's data       |

```python
# Hybrid search example
def hybrid_search(query: str, top_k: int = 5):
    # Semantic search (by meaning)
    semantic_results = vector_store.search(embed(query), limit=20)

    # Keyword search (exact matches)
    keyword_results = bm25_search(query, limit=20)

    # Merge with weighted scoring
    merged = merge_results(
        semantic_results,
        keyword_results,
        semantic_weight=0.7,
        keyword_weight=0.3
    )

    return merged[:top_k]
```

---

### 2. Memory Drift & Inconsistency

**The Problem:**

- Facts can become outdated ("We use MongoDB" → later "We migrated to PostgreSQL")
- Contradictory memories may coexist
- No automatic conflict detection

**Mitigation Strategies:**

| Strategy               | Implementation                                        |
| ---------------------- | ----------------------------------------------------- |
| **Temporal Validity**  | Add `valid_from` and `valid_to` timestamps            |
| **Conflict Detection** | Check for contradictions before adding new facts      |
| **Human Review**       | Flag potential conflicts for manual resolution        |
| **Memory Decay**       | Automatically reduce salience of old, unused memories |

```python
# Conflict detection example
def add_fact(new_fact: str, type: str = "fact"):
    # Search for potentially conflicting facts
    similar = vector_store.search(embed(new_fact), limit=5)

    for existing in similar:
        if similarity(new_fact, existing) > 0.85:
            if is_contradictory(new_fact, existing.content):
                # Mark old fact as superseded
                existing.valid_to = datetime.now()
                existing.superseded_by = new_fact.id
                log_conflict(existing, new_fact)

    # Add new fact
    store(new_fact)
```

---

### 3. Context Window Overflow

**The Problem:**

- Accumulating too much context per request
- Session summaries get too long
- Brain.md grows unbounded

**Mitigation Strategies:**

| Strategy                     | Implementation                                         |
| ---------------------------- | ------------------------------------------------------ |
| **Token Budgeting**          | Hard limit of 2,500 tokens for retrieved context       |
| **Aggressive Summarization** | Compress sessions when > 2,000 tokens                  |
| **Chunked brain.md**         | Split large brain.md into sections, load only relevant |
| **Priority Scoring**         | Only include highest-salience memories                 |

```python
# Token budgeting
MAX_CONTEXT_TOKENS = 2500
TOKEN_BUDGET = {
    "brain_summary": 500,
    "retrieved_facts": 800,
    "decisions": 400,
    "session": 300,
    "user_prefs": 100,
    "buffer": 400  # Safety margin
}

def assemble_context(query: str) -> str:
    context_parts = []
    tokens_used = 0

    for part_name, budget in TOKEN_BUDGET.items():
        content = get_content(part_name, query)
        truncated = truncate_to_tokens(content, budget)
        context_parts.append(truncated)
        tokens_used += count_tokens(truncated)

        if tokens_used >= MAX_CONTEXT_TOKENS:
            break

    return "\n".join(context_parts)
```

---

### 4. MCP Protocol Compatibility

**The Problem:**

- Different clients (Claude, Gemini, Cursor) may have subtle differences
- MCP spec is still evolving
- Transport variations (stdio vs HTTP) have different behaviors

**Mitigation Strategies:**

| Strategy                   | Implementation                              |
| -------------------------- | ------------------------------------------- |
| **Strict Spec Compliance** | Follow MCP spec exactly, no extensions      |
| **Multi-client Testing**   | Test with every major client before release |
| **Graceful Degradation**   | Handle unknown operations without crashing  |
| **Version Negotiation**    | Support multiple MCP versions if needed     |

```python
# Graceful error handling
@mcp_tool("remember")
async def remember(content: str, type: str = "fact"):
    try:
        result = await store_memory(content, type)
        return {"success": True, "id": result.id}
    except ValidationError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"success": False, "error": "Internal error"}
```

---

### 5. Performance Degradation at Scale

**The Problem:**

- Vector search slows with thousands of memories
- Markdown files become unwieldy
- ChromaDB SQLite backend has limits

**Mitigation Strategies:**

| Strategy               | Implementation                             |
| ---------------------- | ------------------------------------------ |
| **Lazy Loading**       | Don't load all memories into RAM           |
| **Index Optimization** | Use HNSW index for fast approximate search |
| **Sharding**           | Split memories by year/month if > 10K      |
| **Archival**           | Move old memories to archive collection    |

```python
# Performance thresholds
PERFORMANCE_CONFIG = {
    "max_active_memories": 5000,
    "archive_after_days": 180,
    "shard_threshold": 10000,
    "search_timeout_ms": 500
}

def periodic_maintenance():
    # Archive old memories
    old_memories = query_memories(
        where={"accessed_at": {"$lt": days_ago(180)}}
    )
    for mem in old_memories:
        move_to_archive(mem)

    # Optimize indexes
    vector_store.optimize()
```

---

### 6. Data Loss & Corruption

**The Problem:**

- ChromaDB corruption if process killed mid-write
- Markdown/Vector DB sync can get out of sync
- User accidentally deletes .0xmemory folder

**Mitigation Strategies:**

| Strategy                        | Implementation                                 |
| ------------------------------- | ---------------------------------------------- |
| **Markdown as Source of Truth** | Vector DB can always be rebuilt from Markdown  |
| **Atomic Writes**               | Write to temp file, then rename                |
| **Startup Validation**          | Check sync on every startup, rebuild if needed |
| **Git as Backup**               | All Markdown is version-controlled             |

```python
# Sync validation on startup
def validate_sync():
    markdown_ids = get_all_markdown_memory_ids()
    vector_ids = get_all_vector_memory_ids()

    if markdown_ids != vector_ids:
        logger.warning("Sync mismatch detected, rebuilding vector DB")
        rebuild_vector_db_from_markdown()

    return True
```

---

### 7. Knowledge Extraction Quality

**The Problem:**

- LLM may extract irrelevant or wrong facts
- Duplicate facts with slightly different wording
- Over-extraction (too many facts from simple conversations)

**Mitigation Strategies:**

| Strategy                  | Implementation                            |
| ------------------------- | ----------------------------------------- |
| **Confidence Thresholds** | Only store high-confidence extractions    |
| **Deduplication**         | Check similarity before adding            |
| **Rate Limiting**         | Max 5 new facts per conversation turn     |
| **Human Review Mode**     | Optional: show extractions before storing |

```python
# Extraction with quality control
def extract_and_store(conversation: str):
    extractions = llm.extract_facts(conversation)

    stored_count = 0
    for fact in extractions:
        # Skip low confidence
        if fact.confidence < 0.7:
            continue

        # Skip duplicates
        if is_duplicate(fact.content):
            continue

        # Rate limit
        if stored_count >= 5:
            break

        store_memory(fact.content, fact.type)
        stored_count += 1

    return stored_count
```

---

### 8. Privacy & Security Concerns

**The Problem:**

- Sensitive info (API keys, passwords) may be stored in memories
- Memories stored in plain text Markdown
- Git history preserves deleted sensitive data

**Mitigation Strategies:**

| Strategy                 | Implementation                                     |
| ------------------------ | -------------------------------------------------- |
| **Content Filtering**    | Detect and redact sensitive patterns               |
| **Privacy Tags**         | User-defined exclusion via `<!-- private -->` tags |
| **Encryption Option**    | Future: encrypt .store/ directory                  |
| **.gitignore Sensitive** | Exclude certain files from Git                     |
| **Memory Expiry**        | Auto-delete memories after configurable period     |

```python
# Sensitive data detection
SENSITIVE_PATTERNS = [
    r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*\S+',
    r'sk-[a-zA-Z0-9]{48}',  # OpenAI keys
    r'AIza[a-zA-Z0-9_-]{35}',  # Google API keys
]

def sanitize_content(content: str) -> str:
    for pattern in SENSITIVE_PATTERNS:
        content = re.sub(pattern, "[REDACTED]", content)
    return content
```

#### Privacy Tags Feature (Inspired by claude-mem)

Allow users to explicitly exclude content from memory storage using HTML comments:

```markdown
## Session Notes

This is a normal note that will be stored in memory.

<!-- private -->

API_KEY=sk-abc123xyz789...
Production database password: supersecret123

<!-- /private -->

This content after the private block is stored normally.
```

**Implementation:**

```python
import re

def strip_private_content(content: str) -> str:
    """
    Remove content between <!-- private --> and <!-- /private --> tags.
    This content will NOT be stored in memory or vector DB.
    """
    pattern = r'<!--\s*private\s*-->.*?<!--\s*/private\s*-->'
    return re.sub(pattern, '[PRIVATE CONTENT EXCLUDED]', content, flags=re.DOTALL)

def process_for_storage(content: str) -> str:
    # First strip private blocks
    content = strip_private_content(content)
    # Then sanitize any remaining sensitive patterns
    content = sanitize_content(content)
    return content
```

**Use Cases:**

- Exclude API keys and credentials shared during debugging
- Hide personal information from memory
- Prevent specific code snippets from being stored
- Keep proprietary algorithms private

---

### 9. Token Cost Visibility (Inspired by claude-mem)

**The Feature:**

Show users how many tokens are being used when retrieving context, enabling informed decisions about memory usage.

**Implementation:**

```python
from transformers import AutoTokenizer

# Load tokenizer once
tokenizer = AutoTokenizer.from_pretrained("gpt2")  # Universal approximation

def count_tokens(text: str) -> int:
    """Count tokens in text."""
    return len(tokenizer.encode(text))

def retrieve_with_cost(query: str, max_tokens: int = 2500) -> dict:
    """
    Retrieve context with token cost breakdown.
    """
    # Retrieve memories
    brain = load_brain_summary()
    facts = search_facts(query, limit=5)
    decisions = search_decisions(query, limit=3)
    session = get_session_summary()

    # Calculate token costs
    costs = {
        "brain_summary": count_tokens(brain),
        "retrieved_facts": count_tokens("\n".join(facts)),
        "decisions": count_tokens("\n".join(decisions)),
        "session_summary": count_tokens(session),
    }

    total = sum(costs.values())

    return {
        "context": assemble_context(brain, facts, decisions, session),
        "token_breakdown": costs,
        "total_tokens": total,
        "budget_remaining": max_tokens - total,
        "budget_used_percent": round((total / max_tokens) * 100, 1)
    }
```

**CLI Display:**

```bash
$ 0xmemory status

🧠 0xMemory Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Facts stored:     42
Decisions logged: 7
Sessions archived: 12

📊 Token Usage (last retrieval):
┌──────────────────┬────────┬───────┐
│ Component        │ Tokens │   %   │
├──────────────────┼────────┼───────┤
│ Brain summary    │    487 │  19%  │
│ Retrieved facts  │    823 │  33%  │
│ Decisions        │    412 │  16%  │
│ Session summary  │    298 │  12%  │
│ Buffer           │    480 │  19%  │
├──────────────────┼────────┼───────┤
│ TOTAL            │  2,500 │ 100%  │
└──────────────────┴────────┴───────┘
```

**Benefits:**

- Users understand token efficiency
- Helps debug context overflow issues
- Enables optimization of memory storage
- Transparency in retrieval process

---

## Technology Justification

### Why These Technologies Were Chosen

#### 1. Python (Language)

| Factor                    | Justification                                                |
| ------------------------- | ------------------------------------------------------------ |
| **Ecosystem**             | Best AI/ML library support (transformers, chromadb, litellm) |
| **MCP SDK**               | Official MCP SDK is Python-first                             |
| **Async Support**         | Native asyncio for MCP server performance                    |
| **Developer Familiarity** | Most AI developers know Python                               |
| **Rapid Prototyping**     | Faster iteration than compiled languages                     |

**Alternatives Considered:**

- **Go:** Better performance, but weaker AI ecosystem
- **TypeScript:** Good for web, but Python has better ML libraries
- **Rust:** Too low-level for rapid development

---

#### 2. ChromaDB (Vector Database)

| Factor            | Justification                            |
| ----------------- | ---------------------------------------- |
| **Local-First**   | Runs embedded, no separate server needed |
| **Lightweight**   | Single SQLite file, easy to backup       |
| **Python Native** | First-class Python support               |
| **Persistent**    | Data survives restarts                   |
| **Free & Open**   | Apache 2.0 license                       |

**Alternatives Considered:**

| Alternative  | Why Not                                 |
| ------------ | --------------------------------------- |
| **Pinecone** | Cloud-only, costs money, vendor lock-in |
| **Weaviate** | Requires running a separate server      |
| **Qdrant**   | Heavier, more complex setup             |
| **FAISS**    | No persistence, just an index library   |
| **LanceDB**  | Newer, less battle-tested               |
| **pgvector** | Requires PostgreSQL server              |

**ChromaDB Benchmarks:**

- **Insert:** ~1000 docs/sec
- **Search:** ~10ms for 10K docs
- **Storage:** ~1KB per embedding (384 dims)

---

#### 3. Sentence Transformers (Embeddings)

| Factor      | Justification                        |
| ----------- | ------------------------------------ |
| **Offline** | No API calls, works without internet |
| **Free**    | No per-token pricing                 |
| **Quality** | Good accuracy for general text       |
| **Speed**   | Fast inference on CPU                |
| **Variety** | Many model sizes to choose from      |

**Model Comparison:**

| Model               | Size  | Quality | Speed  | Use Case               |
| ------------------- | ----- | ------- | ------ | ---------------------- |
| `all-MiniLM-L6-v2`  | 80MB  | Good    | Fast   | **Default choice**     |
| `all-mpnet-base-v2` | 420MB | Better  | Medium | Higher accuracy needed |
| `nomic-embed-text`  | 550MB | Best    | Slower | Quality-critical apps  |

**Why not cloud embeddings (OpenAI, Gemini)?**

- Cost per token adds up
- Requires internet connection
- Privacy (sending all your data to cloud)
- Latency from API calls

---

#### 4. MCP Protocol (Integration)

| Factor                | Justification                                       |
| --------------------- | --------------------------------------------------- |
| **Universal**         | Works with Claude, Gemini, Cursor, and future tools |
| **Official Standard** | Backed by Anthropic, adopted by Google              |
| **Simple**            | JSON-RPC over stdio/HTTP, easy to implement         |
| **Extensible**        | Tools, Resources, Prompts—covers all use cases      |
| **No Lock-in**        | Open spec, not tied to any vendor                   |

**Why MCP instead of custom API?**

- No need to build integrations for each LLM client
- Future-proof as more tools adopt MCP
- Users can switch LLMs without changing memory

---

#### 5. Typer + Rich (CLI)

| Factor            | Justification                                     |
| ----------------- | ------------------------------------------------- |
| **Type Hints**    | Auto-generates help, validation from Python types |
| **Rich Output**   | Beautiful tables, colors, progress bars           |
| **Minimal Code**  | Less boilerplate than argparse/click              |
| **Auto-Complete** | Shell completions generated automatically         |

```python
# Compare: Typer vs argparse

# argparse (verbose)
parser = argparse.ArgumentParser()
parser.add_argument('--name', type=str, required=True)
args = parser.parse_args()

# Typer (clean)
@app.command()
def greet(name: str):
    print(f"Hello {name}")
```

---

#### 6. Pydantic (Validation)

| Factor             | Justification                           |
| ------------------ | --------------------------------------- |
| **Type Safety**    | Validates all data at runtime           |
| **Serialization**  | Easy JSON/YAML conversion               |
| **IDE Support**    | Autocomplete works with Pydantic models |
| **Error Messages** | Clear validation error messages         |

```python
# Config validation with Pydantic
class MemoryConfig(BaseModel):
    content: str
    type: Literal["fact", "decision", "learning"]
    tags: list[str] = []
    salience: float = Field(ge=0.0, le=1.0, default=0.5)

# Automatically validates
memory = MemoryConfig(content="...", type="fact", salience=1.5)
# Raises: ValidationError: salience must be <= 1.0
```

---

#### 7. LiteLLM (LLM Abstraction)

| Factor               | Justification                                       |
| -------------------- | --------------------------------------------------- |
| **Unified API**      | Same code works with OpenAI, Gemini, Claude, Ollama |
| **Fallback Support** | Auto-retry with different providers                 |
| **Local Support**    | Works with Ollama for offline operation             |
| **Cost Tracking**    | Built-in token counting and cost estimation         |

```python
# Works with ANY provider
from litellm import completion

# These all use the same API:
completion(model="gpt-4")
completion(model="gemini/gemini-2.0-flash")
completion(model="claude-3-sonnet-20240229")
completion(model="ollama/llama3")
```

**Why not use provider SDKs directly?**

- Would need separate code for each provider
- Harder to implement fallback logic
- More maintenance as APIs evolve

---

#### 8. SQLite (Metadata)

| Factor          | Justification                     |
| --------------- | --------------------------------- |
| **Zero Config** | No server, just a file            |
| **Reliable**    | Billions of deployments worldwide |
| **Fast**        | Great for read-heavy workloads    |
| **Portable**    | Single file, easy to backup       |
| **Built-in**    | Comes with Python                 |

**Why not PostgreSQL?**

- Requires running a server
- Overkill for single-user local app
- More complex deployment

---

### Technology Stack Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    0xMemory Technology Stack                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INTERFACE LAYER                                                 │
│  ├── MCP Protocol   → Cross-LLM compatibility                   │
│  └── Typer + Rich   → Beautiful CLI                             │
│                                                                  │
│  LOGIC LAYER                                                     │
│  ├── Python 3.11+   → Async, type hints, ecosystem              │
│  ├── Pydantic       → Data validation                           │
│  └── LiteLLM        → Multi-provider LLM access                 │
│                                                                  │
│  STORAGE LAYER                                                   │
│  ├── ChromaDB       → Vector search (embeddings)                │
│  ├── SQLite         → Metadata, indexes                         │
│  └── Markdown       → Human-readable, Git-friendly              │
│                                                                  │
│  EMBEDDING LAYER                                                 │
│  └── Sentence-Transformers → Local, fast, free                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Open Questions & Future Considerations

### Resolved in This Design

| Question                         | Resolution                            |
| -------------------------------- | ------------------------------------- |
| How to share memory across LLMs? | MCP protocol + shared storage         |
| How to handle token limits?      | Smart retrieval, ~2.5K tokens/request |
| How to work offline?             | Local embeddings, local vector DB     |
| How to keep data portable?       | Markdown source of truth, Git-native  |

### Still Open

| Question                      | Possible Approaches                       |
| ----------------------------- | ----------------------------------------- |
| **Multi-project memory?**     | Global brain + project-specific brains    |
| **Sensitive data handling?**  | Pattern detection + optional encryption   |
| **Team collaboration?**       | Git-based merging, conflict resolution UI |
| **Memory schema migrations?** | Version field + migration scripts         |
| **Very large projects?**      | Sharding by module/component              |
| **Real-time sync?**           | Filesystem watcher + incremental indexing |

### Future Enhancements (Post v1.0)

| Feature                   | Value                         | Complexity |
| ------------------------- | ----------------------------- | ---------- |
| **GraphRAG**              | Better relationship reasoning | High       |
| **Web Dashboard**         | Visual memory exploration     | Medium     |
| **VS Code Extension**     | Inline memory suggestions     | Medium     |
| **Fine-tuned Embeddings** | Better domain-specific search | High       |
| **Memory Visualizer**     | Graph view of connections     | Medium     |
| **Team Sync**             | Shared team brains            | High       |

---

## Next Steps

1. ✅ Research complete
2. ✅ Strategy documented
3. ⏳ Implement Phase 1 (MCP Foundation)
4. ⏳ Implement Phase 2 (Vector Search)
5. ⏳ Implement Phase 3 (Knowledge Extraction)
6. ⏳ Polish and release

---

_This is a living document. Update as implementation progresses._
