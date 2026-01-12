# 0xMemory Client Configuration Guide

Connect your favorite AI editors and tools to 0xMemory.

---

## 1. Claude Desktop (Stdio)

Claude Desktop connects to 0xMemory via standard input/output (stdio). This runs the server locally as a subprocess.

### Configuration

Edit your Claude Desktop configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add `0xmemory` to the `mcpServers` object:

```json
{
  "mcpServers": {
    "0xmemory": {
      "command": "/path/to/venv/bin/0xmemory",
      "args": ["serve", "/path/to/your/project"],
      "env": {
        "OLLAMA_API_BASE": "http://localhost:11434"
      }
    }
  }
}
```

> **Tip:** Use `which 0xmemory` inside your project's virtual environment to get the full path.

### Verification

1. Restart Claude Desktop.
2. Look for the plug icon 🔌 in the input bar.
3. You should see `0xmemory` tools listed (`remember`, `recall`, etc.).

---

## 2. Cursor (HTTP / SSE)

Cursor can connect via HTTP (Server-Sent Events), which is useful if you want to run the server in a terminal and have Cursor connect to it.

### Step 1: Start Server

Run the server in a terminal window:

```bash
cd /path/to/project
0xmemory serve --transport http --port 8000
```

### Step 2: Configure Cursor

1. Open Cursor Settings (Cmd+Shift+J or Ctrl+Shift+J).
2. Go to **Features** -> **MCP**.
3. Click **Add New MCP Server**.
4. Enter:
   - **Name:** `0xmemory`
   - **Type:** `SSE`
   - **URL:** `http://localhost:8000/sse`

### Verification

Check the MCP status indicator in Cursor. It should show solid green.

---

## 3. Gemini (Python Client)

Currently, Google's Gemini CLI does not directly support generic MCP servers. However, you can use the Python SDK to build custom tools dependent on 0xMemory.

### Example Client Script

See `examples/gemini_client.py` in the 0xMemory repository for a full working example of how to connect a Gemini model to the MCP server.

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ... check repo for full code ...
```

---

## 4. Other Clients

For any client that supports MCP:

- **Stdio:** Point the command to your `0xmemory` executable.
- **SSE:** Run `0xmemory serve --transport http` and point the client to the `/sse` endpoint.
