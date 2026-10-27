"""Read-only SDK smoke check for a freshly prepared To-do brain."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def check(project, transport):
    client = stdio_client
    if transport == "anonymous":
        # Explicit diagnostic adapter; never silently downgrade native transport.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from tests.stdio_anonymous import anonymous_stdio_client

        client = anonymous_stdio_client
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "oxmemory", "serve", str(project)],
        env={"PYTHONUTF8": "1", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
    )
    async with asyncio.timeout(90):
        async with client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                assert initialized.server_info.name == "0xmemory"
                names = {tool.name for tool in (await session.list_tools()).tools}
                expected = {
                    "remember",
                    "recall",
                    "list",
                    "forget",
                    "update",
                    "status",
                    "extract",
                    "observe_commit",
                    "verify_memory",
                    "supersede_memory",
                }
                assert expected <= names, names
                response = await session.call_tool("status", {})
                assert not response.is_error, response
                status = json.loads(next(c.text for c in response.content if c.type == "text"))
                assert status["project_name"] == project.name, status
                assert status["total_memories"] == 0, status
                assert Path(status["brain_path"]).resolve() == project / ".0xmemory", status
                return dict(transport=transport, tools=sorted(names), status=status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--transport", choices=["native", "anonymous"], default="native")
    args = parser.parse_args()
    result = asyncio.run(check(args.project.resolve(), args.transport))
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS: real MCP discovery and correct zero-memory project status")
