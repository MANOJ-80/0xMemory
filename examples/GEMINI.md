# GEMINI.md - Gemini CLI Context

> Copy this file to your project root for Gemini CLI integration.

## 0xMemory Integration

This project uses **0xMemory** for persistent AI memory across sessions.

### How It Works

1. Start the memory server: `0xmemory serve`
2. Gemini connects via MCP protocol
3. Use tools to save and recall information

### Available Tools

**Saving Information:**

```
Use the remember tool:
- type: fact | decision | learning | preference
- content: The information to save
- tags: Optional comma-separated tags
```

**Finding Information:**

```
Use the recall tool:
- query: Natural language search query
- limit: Number of results (default: 5)
```

**Other Tools:**

- `list` - View all memories
- `forget` - Delete by ID
- `update` - Modify existing
- `extract` - Parse knowledge from text

### Resources

Read project context from:

- `brain://context` - Main project brain
- `brain://facts` - Technical facts
- `brain://decisions` - Decision log

## Instructions for Gemini

1. **Check Memory** - Use `recall` before requesting context
2. **Save Knowledge** - Use `remember` for important information
3. **Stay Updated** - Use `update` when facts change
4. **Be Helpful** - Proactively save valuable discussions

---

## Project Information

<!-- ADD YOUR PROJECT CONTEXT BELOW -->

### About This Project

[Description]

### Stack

[Technologies used]

### Structure

[Key directories and files]

### Guidelines

[Coding standards]
