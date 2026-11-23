"""
MCP client wrapper.

Launches mcp_server/server.py as a subprocess and speaks real MCP
(stdio transport, JSON-RPC under the hood — handled by the `mcp` SDK)
to it. This is the ONLY file that opens an MCP `ClientSession`; every
LangChain tool in `langchain_tools.py` calls through this module, never
around it.

Sync wrapper is provided because LangGraph nodes in this build are sync
functions — MCP's SDK is async-native, so we run each call on a short-lived
event loop. For a long-running server (Phase B+), swap this for one
persistent asyncio loop / async LangGraph nodes.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "mcp_server", "server.py")


async def _call_tool_async(tool_name: str, arguments: dict) -> dict:
    params = StdioServerParameters(command=sys.executable, args=[_SERVER_SCRIPT], env=None)
    async with AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(stdio_client(params))
        session: ClientSession = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        result = await session.call_tool(tool_name, arguments=arguments)
        text = result.content[0].text if result.content else "{}"
        return json.loads(text)


def call_mcp_tool(tool_name: str, **arguments) -> dict:
    """Synchronous entry point used by every LangChain tool wrapper."""
    return asyncio.run(_call_tool_async(tool_name, arguments))


# Thin, explicit wrappers (kept 1:1 with the MCP server's tool names) so
# call sites read as "MCP tool calls", not generic dict lookups.
def mcp_read_curriculum(course_code: str | None = None) -> dict:
    return call_mcp_tool("read_curriculum", course_code=course_code)


def mcp_read_industry_signals() -> dict:
    return call_mcp_tool("read_industry_signals")


def mcp_read_student_performance(course_code: str | None = None) -> dict:
    return call_mcp_tool("read_student_performance", course_code=course_code)


def mcp_read_revision_history(tag: str | None = None) -> dict:
    return call_mcp_tool("read_revision_history", tag=tag)


def mcp_read_accreditation_reference() -> dict:
    return call_mcp_tool("read_accreditation_reference")


async def _list_tools_async() -> list[dict]:
    params = StdioServerParameters(command=sys.executable, args=[_SERVER_SCRIPT], env=None)
    async with AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(stdio_client(params))
        session: ClientSession = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        tools = await session.list_tools()
        resources = await session.list_resources()
        out = [{"kind": "tool", "name": t.name, "description": (t.description or "").strip().split("\n")[0]} for t in tools.tools]
        out += [{"kind": "resource", "name": str(r.uri), "description": (r.description or "").strip().split("\n")[0]} for r in resources.resources]
        return out


def list_mcp_capabilities() -> list[dict]:
    """Live MCP discovery (tools/list + resources/list) -- shown in the app as
    an in-app equivalent of the MCP Inspector."""
    return asyncio.run(_list_tools_async())
