# CLAUDE.md - Claude Code Context

> Copy this file to your project root to provide context to Claude Code/Claude Desktop.

## Project Memory System

This project uses **0xMemory** for persistent, cross-session memory.
Memory is stored in `.0xmemory/` and accessible via MCP tools.

## Memory Tools

When you need to remember or recall information, use these tools:

- **`remember`** - Store facts, decisions, preferences, learnings
- **`recall`** - Semantic search through past memories
- **`list`** - View all stored memories
- **`forget`** - Remove outdated memories
- **`update`** - Modify existing memories
- **`extract`** - Parse knowledge from text blocks

## Memory Resources

Read-only context available:

- `brain://context` - Project overview and goals
- `brain://facts` - Technical facts
- `brain://decisions` - Architectural decision log
- `brain://full` - Complete context

## Guidelines

1. **Search Before Asking** - Use `recall` before requesting repeated context
2. **Save Decisions** - When we make architectural choices, save them with reasoning
3. **Update Outdated Info** - If you notice facts have changed, use `update`
4. **Proactive Memory** - Offer to remember important discussions

## Project Context

<!-- CUSTOMIZE: Add your project-specific context below -->

### Overview

[Describe your project here]

### Tech Stack

[List your technologies]

### Architecture

[Describe key components]

### Conventions

[List coding standards and patterns]

### Current Focus

[What you're currently working on]
