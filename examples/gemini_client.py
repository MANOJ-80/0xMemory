"""Gemini MCP Client for Testing.

This script demonstrates how to connect a Gemini model to the 0xMemory MCP server
via stdio transport using the mcp-python SDK.
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, "/home/itachi/Projects/0xMemory/src")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

STDLIB_TOOLS = {
    "remember": "Store a memory",
    "recall": "Search memories",
    "list": "List all memories",
    "status": "Check brain status"
}

async def run_client():
    # 1. Start the MCP server subprocess
    # We use the raw python command to run the server module
    server_params = StdioServerParameters(
        command="python3",
        args=["-m", "oxmemory.cli.main", "serve", "test-gemini"],
        env=os.environ.copy(),
    )

    print("🔌 Connecting to 0xMemory MCP server...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 2. List available tools
            tools = await session.list_tools()
            print(f"\n✅ Connected! Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # 3. Simulate a Gemini interaction
            # (In a real app, you would pass tool schemas to the model)
            print("\n🤖 Simulating Gemini interaction...")

            # Scenario: User says "I learned that FastAPI is great for async apps"
            print("\n> User: I learned that FastAPI is great for async apps")

            # Manually call tool for demonstration (simulating model output)
            print("  [Gemini decides to call 'remember' tool]")

            result = await session.call_tool(
                "remember",
                arguments={
                    "content": "FastAPI is great for async apps",
                    "type": "learning",
                    "tags": ["python", "web"],
                    "source": "user"
                }
            )

            print(f"  ✅ Tool Result: {result.content[0].text}")

            # Scenario: User asks "What do we know about FastAPI?"
            print("\n> User: What do we know about FastAPI?")
            print("  [Gemini decides to call 'recall' tool]")

            result = await session.call_tool(
                "recall",
                arguments={"query": "FastAPI"}
            )

            print(f"  ✅ Tool Result: {result.content[0].text}")

            print("\n✨ Test complete!")

if __name__ == "__main__":
    # Check for GEMINI_API_KEY (though we mock the actual generation for now
    # to avoid rate limits, this script structure is what a client uses)
    asyncio.run(run_client())
