# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-01-12

### Changed

- **Lightweight Default**: Reverted to a minimal dependency set (removed `torch`, `chromadb`, etc. from default install).
- **Optional Extras**: Use `pip install oxmemory[all]` for full local features. Standard install is now API-first and small (~5MB).
- **Dependencies**: Added `python-dotenv` to core for secure configuration.

## [1.0.1] - 2026-01-12

### Changed

- **Dependencies**: Made `oxmemory` "batteries-included" by moving all optional dependencies (chromadb, litellm, fastapi, etc.) to core dependencies.
- **Install**: `pip install oxmemory` now installs everything needed for vector search and HTTP server.

## [1.0.0] - 2026-01-12

### Added

#### Core Features

- **MCP Server**: Full Model Context Protocol implementation with stdio and HTTP/SSE transports
- **Dual Storage**: Markdown files (human-editable) + ChromaDB vectors (semantic search)
- **Memory Types**: Support for facts, decisions, learnings, and preferences
- **Vector Search**: Semantic search using `sentence-transformers` (all-MiniLM-L6-v2)
- **Knowledge Extraction**: LLM-based fact/decision extraction from conversations

#### MCP Tools

- `remember` - Store new memories with type, tags, and source
- `recall` - Semantic search through memories
- `list` - List all memories with optional filters
- `forget` - Remove memories by ID
- `update` - Update existing memory content
- `status` - Get brain statistics
- `extract` - Extract knowledge from conversations using LLM

#### MCP Resources

- `brain://context` - Main project brain (brain.md)
- `brain://facts` - All stored facts
- `brain://decisions` - Decision log
- `brain://full` - Combined full context

#### CLI Commands

- `0xmemory init` - Initialize brain in current directory
- `0xmemory serve` - Start MCP server (stdio or http)
- `0xmemory status` - View brain statistics
- `0xmemory add` - Manually add memories
- `0xmemory forget` - Delete a memory by ID
- `0xmemory update` - Update a memory's content
- `0xmemory search` - Search through memories
- `0xmemory extract` - Extract knowledge from text
- `0xmemory rebuild` - Rebuild vector index from Markdown
- `0xmemory export` - Export memories to JSON/CSV
- `0xmemory config` - View configuration
- `0xmemory doctor` - Run health checks on brain configuration

#### LLM Provider Support

- Ollama (local, recommended for development)
- Groq (free tier: 14,400 req/day)
- OpenRouter
- Gemini (Google AI Studio)

#### Client Compatibility

- Claude Desktop (stdio transport)
- Cursor IDE (HTTP/SSE transport)
- Gemini CLI (via Python client)
- Any MCP-compliant client

#### Developer Experience

- `--debug` flag for verbose logging in serve command
- `/health` endpoint for HTTP mode (load balancer support)
- Auto-update of `.gitignore` during init (adds `.0xmemory/.store/`)
- Comprehensive `doctor` command for configuration validation

### Documentation

- [README.md](README.md) - Quick start and usage guide
- [docs/how_it_works.md](docs/how_it_works.md) - Architecture deep dive
- [docs/testing_guide.md](docs/testing_guide.md) - Real-world testing scenarios
- [docs/client_config.md](docs/client_config.md) - Client configuration guide
- [docs/prerequisites.md](docs/prerequisites.md) - Learning resources
- [docs/implementation_strategy.md](docs/implementation_strategy.md) - Full technical spec
- [docs/research_findings.md](docs/research_findings.md) - Competitive analysis

---

## [Unreleased]

### Planned

- Memory decay and consolidation
- Cloud sync (S3/GCS backup)
- Additional IDE adapters (VS Code, JetBrains)
- Memory import from Mem0, Zep, SuperMemory

---

[1.0.0]: https://github.com/MANOJ-80/0xMemory/releases/tag/v1.0.0
[Unreleased]: https://github.com/MANOJ-80/0xMemory/compare/v1.0.0...HEAD
