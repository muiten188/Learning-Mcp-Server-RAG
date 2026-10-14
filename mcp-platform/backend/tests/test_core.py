import asyncio

from app.services.mcp_tools import call_tool, ollama_tools, tool_session
from app.services.orchestrator import event
from app.services.rag import chunks


def test_chunk_overlap_and_stream_format():
    pieces = chunks("a" * 1300)
    assert len(pieces) == 2
    assert pieces[0][-150:] == pieces[1][:150]
    assert event("token", {"text": "hi"}) == 'event: token\ndata: {"text": "hi"}\n\n'


def test_mcp_tools_roundtrip():
    async def check():
        async with tool_session() as session:
            names = {item["function"]["name"] for item in await ollama_tools(session)}
            assert {
                "create_file",
                "list_files",
                "read_file",
                "get_weather",
                "crawl_webpage",
            } <= names
            result, is_error = await call_tool(session, "list_files", {})
            assert not is_error
            assert "workspace" in result.lower()

    asyncio.run(check())
