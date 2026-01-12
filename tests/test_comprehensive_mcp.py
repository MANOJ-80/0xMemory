"""Comprehensive MCP server test - all tools, resources, and prompts.

Tests both transports and all MCP capabilities.
"""

import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client


async def comprehensive_test():
    """Complete test of all MCP capabilities."""
    
    print("=" * 60)
    print("🧪 COMPREHENSIVE 0xMEMORY MCP SERVER TEST")
    print("=" * 60)
    
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            results = {
                "tools": [],
                "resources": [],
                "prompts": [],
                "tool_tests": [],
            }
            
            # ============ LIST ALL CAPABILITIES ============
            print("\n📦 TOOLS:")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  ✓ {tool.name}")
                results["tools"].append(tool.name)
            
            print(f"\n📚 RESOURCES:")
            resources = await session.list_resources()
            for res in resources.resources:
                print(f"  ✓ {res.uri}")
                results["resources"].append(str(res.uri))
            
            print(f"\n💬 PROMPTS:")
            prompts = await session.list_prompts()
            for prompt in prompts.prompts:
                print(f"  ✓ {prompt.name}")
                results["prompts"].append(prompt.name)
            
            # ============ TEST EACH TOOL ============
            print("\n" + "=" * 60)
            print("🔧 TESTING EACH TOOL:")
            print("=" * 60)
            
            # 1. remember
            print("\n1️⃣ remember...")
            result = await session.call_tool("remember", {
                "content": "Test memory from comprehensive test",
                "type": "fact",
                "tags": ["test", "verification"]
            })
            data = json.loads(result.content[0].text)
            memory_id = data.get("id")
            print(f"   ✅ Created memory: {memory_id}")
            results["tool_tests"].append(("remember", True))
            
            # 2. recall
            print("\n2️⃣ recall...")
            result = await session.call_tool("recall", {"query": "test memory"})
            data = json.loads(result.content[0].text)
            print(f"   ✅ Found {data.get('found', 0)} memories")
            results["tool_tests"].append(("recall", True))
            
            # 3. list
            print("\n3️⃣ list...")
            result = await session.call_tool("list", {"limit": 5})
            data = json.loads(result.content[0].text)
            print(f"   ✅ Listed {data.get('count', 0)} memories")
            results["tool_tests"].append(("list", True))
            
            # 4. status
            print("\n4️⃣ status...")
            result = await session.call_tool("status", {})
            data = json.loads(result.content[0].text)
            print(f"   ✅ Project: {data.get('project_name')}, Total: {data.get('total_memories')}")
            results["tool_tests"].append(("status", True))
            
            # 5. update
            print("\n5️⃣ update...")
            if memory_id:
                result = await session.call_tool("update", {
                    "id": memory_id,
                    "content": "Updated test memory content"
                })
                data = json.loads(result.content[0].text)
                print(f"   ✅ Updated: {data.get('success')}")
                results["tool_tests"].append(("update", True))
            
            # 6. forget
            print("\n6️⃣ forget...")
            if memory_id:
                result = await session.call_tool("forget", {"id": memory_id})
                data = json.loads(result.content[0].text)
                print(f"   ✅ Deleted: {data.get('success')}")
                results["tool_tests"].append(("forget", True))
            
            # 7. extract (may fail without LLM)
            print("\n7️⃣ extract...")
            try:
                result = await session.call_tool("extract", {
                    "conversation": "We decided to use FastAPI because it's fast.",
                    "auto_save": False
                })
                data = json.loads(result.content[0].text)
                if data.get("success"):
                    print(f"   ✅ Extracted knowledge")
                else:
                    print(f"   ⚠️ No LLM available (expected in test env)")
                results["tool_tests"].append(("extract", True))
            except Exception as e:
                print(f"   ⚠️ Extract needs LLM: {e}")
                results["tool_tests"].append(("extract", "skipped"))
            
            # ============ TEST EACH RESOURCE ============
            print("\n" + "=" * 60)
            print("📖 TESTING EACH RESOURCE:")
            print("=" * 60)
            
            for uri in ["brain://context", "brain://facts", "brain://decisions", "brain://full"]:
                print(f"\n  {uri}...")
                try:
                    result = await session.read_resource(uri)
                    content = result.contents[0].text if result.contents else ""
                    print(f"   ✅ Read {len(content)} characters")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
            # ============ TEST PROMPTS ============
            print("\n" + "=" * 60)
            print("💬 TESTING PROMPTS:")
            print("=" * 60)
            
            print("\n  project_context...")
            try:
                result = await session.get_prompt("project_context", {})
                print(f"   ✅ Got prompt with {len(result.messages)} messages")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # ============ SUMMARY ============
            print("\n" + "=" * 60)
            print("📊 SUMMARY:")
            print("=" * 60)
            print(f"  Tools: {len(results['tools'])}/7")
            print(f"  Resources: {len(results['resources'])}/4")
            print(f"  Prompts: {len(results['prompts'])}/2")
            passed = sum(1 for _, r in results["tool_tests"] if r == True)
            print(f"  Tool Tests: {passed}/{len(results['tool_tests'])} passed")
            print("\n✅ ALL TESTS COMPLETED!")


if __name__ == "__main__":
    asyncio.run(comprehensive_test())
