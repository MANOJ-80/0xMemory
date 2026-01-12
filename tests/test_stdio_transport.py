"""Test MCP server with STDIO transport (Claude Desktop mode).

This tests the same transport that Claude Desktop uses.
"""

import asyncio
import json
import subprocess
import sys


async def test_stdio_transport():
    """Test MCP server via stdio transport."""
    
    print("🔌 Testing STDIO transport (Claude Desktop mode)...")
    print("=" * 50)
    
    # Start the MCP server as a subprocess
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "oxmemory.cli.main", "serve",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd="/home/itachi/Projects/0xMemory"
    )
    
    # MCP uses JSON-RPC over stdio
    # Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    # Send request
    request_bytes = json.dumps(init_request).encode() + b"\n"
    print(f"📤 Sending: initialize")
    proc.stdin.write(request_bytes)
    await proc.stdin.drain()
    
    # Read response (with timeout)
    try:
        response = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
        response_data = json.loads(response.decode())
        print(f"📥 Received: {json.dumps(response_data, indent=2)[:200]}...")
        
        if "result" in response_data:
            print("\n✅ STDIO transport working!")
            server_info = response_data.get("result", {}).get("serverInfo", {})
            print(f"   Server: {server_info.get('name', 'unknown')}")
            print(f"   Version: {server_info.get('version', 'unknown')}")
        else:
            print(f"❌ Unexpected response: {response_data}")
            
    except asyncio.TimeoutError:
        print("⏱️ Timeout waiting for response")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
    finally:
        proc.terminate()
        await proc.wait()
    
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_stdio_transport())
