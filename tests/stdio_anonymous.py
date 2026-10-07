"""Real stdio transport for tests in Windows sandboxes that restrict named pipes.

The MCP SDK still handles protocol messages and ClientSession. Only subprocess
pipe I/O uses ordinary Popen pipes and worker threads instead of asyncio's
overlapped Windows named pipes. No server or response is mocked.
"""

import asyncio
import os
import subprocess
import sys
from contextlib import asynccontextmanager

import anyio
import mcp.types as types
from mcp.shared.message import SessionMessage


@asynccontextmanager
async def anonymous_stdio_client(parameters):
    process = subprocess.Popen(
        [parameters.command, *parameters.args],
        env=dict(os.environ) | (parameters.env or {}),
        cwd=parameters.cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=sys.stderr,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    incoming, read = anyio.create_memory_object_stream(8)
    write, outgoing = anyio.create_memory_object_stream(8)
    writer_done = anyio.Event()

    async def receive():
        async with incoming:
            while line := await asyncio.to_thread(process.stdout.readline):
                try:
                    message = SessionMessage(types.jsonrpc_message_adapter.validate_json(line))
                except ValueError as exc:
                    message = exc
                await incoming.send(message)

    def send_line(message):
        payload = message.message.model_dump_json(by_alias=True, exclude_unset=True)
        process.stdin.write((payload + "\n").encode("utf-8"))
        process.stdin.flush()

    async def send():
        try:
            async with outgoing:
                async for message in outgoing:
                    await asyncio.to_thread(send_line, message)
        finally:
            writer_done.set()

    try:
        async with anyio.create_task_group() as group:
            group.start_soon(receive)
            group.start_soon(send)
            try:
                yield read, write
            finally:
                with anyio.CancelScope(shield=True):
                    write.close()
                    with anyio.move_on_after(3):
                        await writer_done.wait()
                    process.stdin.close()
                    try:
                        await asyncio.to_thread(process.wait, timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        await asyncio.to_thread(process.wait, timeout=5)
                    group.cancel_scope.cancel()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()
        process.stdin.close()
        for stream in (incoming, read, write, outgoing):
            stream.close()
