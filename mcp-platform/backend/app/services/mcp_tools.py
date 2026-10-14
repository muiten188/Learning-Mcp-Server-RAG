import sys
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.config import get_settings


@asynccontextmanager
async def tool_session():
    path = get_settings().server_path
    params = StdioServerParameters(
        command=sys.executable, args=[str(path)], cwd=str(path.parent)
    )
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            yield session


async def ollama_tools(session) -> list[dict]:
    result = await session.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }
        for tool in result.tools
    ]


async def call_tool(session, name: str, args: dict) -> tuple[str, bool]:
    result = await session.call_tool(name, args)
    content = "\n".join(getattr(item, "text", "") for item in result.content)
    return content or "(no output)", bool(result.is_error)
