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

1. [Design Philosophy](#design-philosophy)
2. [System Architecture](#system-architecture)
3. [MCP Server Design](#mcp-server-design)
4. [Memory Architecture](#memory-architecture)
5. [Cross-LLM Strategy](#cross-llm-strategy)
6. [Infinite Context Strategy](#infinite-context-strategy)
7. [Technical Stack](#technical-stack)
8. [Implementation Phases](#implementation-phases)
9. [File & Data Structures](#file--data-structures)
10. [API Specification](#api-specification)
11. [Testing Strategy](#testing-strategy)

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

## Risks & Mitigations

| Risk                        | Mitigation                                       |
| --------------------------- | ------------------------------------------------ |
| **Embedding quality**       | Allow swappable models, default to battle-tested |
| **Context overflow**        | Aggressive compression, token budgeting          |
| **MCP compatibility**       | Follow spec strictly, test with all clients      |
| **Git conflicts**           | Structured Markdown, atomic commits              |
| **Performance degradation** | Lazy loading, index optimization                 |

---

## Open Questions

1. **Multi-project:** How to handle cross-project memory sharing?
2. **Privacy:** How to handle sensitive information in memories?
3. **Collaboration:** How to merge team-member brains?
4. **Versioning:** How to handle memory schema migrations?

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
