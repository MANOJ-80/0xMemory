"""Manual MCP server test using Python client.

Run this while the server is running:
    0xmemory serve --transport http --port 8000
"""

import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client


async def test_mcp_server():
    """Test MCP server with all tools and resources."""
    
    print("🔌 Connecting to MCP server at http://localhost:8000/sse...")
    
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected!\n")
            
            # Test 1: List available tools
            print("=" * 50)
            print("📦 Available Tools:")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description[:50]}...")
            
            # Test 2: List available resources
            print("\n" + "=" * 50)
            print("📚 Available Resources:")
            resources = await session.list_resources()
            for res in resources.resources:
                print(f"  - {res.uri}: {res.name}")
            
            # Test 3: Test 'remember' tool
            print("\n" + "=" * 50)
            print("🧠 Testing 'remember' tool...")
            result = await session.call_tool("remember", {
                "content": "The project uses FastAPI for the HTTP server",
                "type": "fact",
                "tags": ["api", "framework"]
            })
            print(f"  Result: {result.content[0].text}")
            
            # Test 4: Test 'recall' tool
            print("\n" + "=" * 50)
            print("🔍 Testing 'recall' tool...")
            result = await session.call_tool("recall", {
                "query": "HTTP server",
                "limit": 3
            })
            print(f"  Result: {result.content[0].text}")
            
            # Test 5: Test 'status' tool
            print("\n" + "=" * 50)
            print("📊 Testing 'status' tool...")
            result = await session.call_tool("status", {})
            print(f"  Result: {result.content[0].text}")
            
            # Test 6: Read a resource
            print("\n" + "=" * 50)
            print("📖 Reading 'brain://context' resource...")
            result = await session.read_resource("brain://context")
            content = result.contents[0].text if result.contents else "No content"
            print(f"  Content preview: {content[:200]}...")
            
            # Test 7: Test 'list' tool
            print("\n" + "=" * 50)
            print("📋 Testing 'list' tool...")
            result = await session.call_tool("list", {"limit": 5})
            print(f"  Result: {result.content[0].text}")
            
            print("\n" + "=" * 50)
            print("✅ All MCP tests passed!")
            print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
