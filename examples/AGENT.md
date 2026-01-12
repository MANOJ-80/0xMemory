# AGENT.md - Universal AI Agent Context

> This file provides context for any AI coding assistant using 0xMemory.

## Memory System

This project has **persistent memory** via 0xMemory MCP server.

### Quick Reference

| Action     | Tool       | Example                          |
| ---------- | ---------- | -------------------------------- |
| Save info  | `remember` | Remember that we use JWT auth    |
| Find info  | `recall`   | Search for "authentication"      |
| List all   | `list`     | Show all facts                   |
| Delete     | `forget`   | Remove mem-12345                 |
| Update     | `update`   | Change mem-12345 to new content  |
| Parse text | `extract`  | Extract facts from meeting notes |

### Resources

| URI                 | Description                 |
| ------------------- | --------------------------- |
| `brain://context`   | Project overview (brain.md) |
| `brain://facts`     | All technical facts         |
| `brain://decisions` | Decision log with reasoning |
| `brain://full`      | Everything combined         |

## Behavior Guidelines

### Always Do

- ✅ Check `recall` before saying "I don't know"
- ✅ Save important technical decisions
- ✅ Update facts when they change
- ✅ Reference past context when relevant

### Never Do

- ❌ Ask user to repeat context you should remember
- ❌ Assume memory is empty without checking
- ❌ Ignore saved preferences or conventions

## Memory Types

| Type         | Use For             | Examples                                |
| ------------ | ------------------- | --------------------------------------- |
| `fact`       | Technical details   | "API port is 8080", "Using Python 3.11" |
| `decision`   | Choices + reasoning | "Chose Postgres for better joins"       |
| `learning`   | Lessons, gotchas    | "Don't use sync in async handlers"      |
| `preference` | Style preferences   | "Use Pydantic v2 for models"            |

---

## Project Context

<!-- CUSTOMIZE BELOW -->

### Project Name

[Your project name]

### Description

[What this project does]

### Key Technologies

- [Technology 1]
- [Technology 2]

### Important Patterns

- [Pattern or convention]

### Current Sprint/Focus

[What's being worked on now]
