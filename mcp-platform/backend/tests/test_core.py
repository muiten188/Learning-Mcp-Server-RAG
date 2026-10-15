import asyncio

from app.features.chat.orchestrator import available_tools, event, requested_web_url
from app.features.mcp.client import call_tool, ollama_tools, tool_session
from app.features.rag.service import chunks


def test_chunk_overlap_and_stream_format() -> None:
    """Preserve chunk overlap and SSE serialization."""
    pieces = chunks("a" * 1300)
    assert len(pieces) == 2
    assert pieces[0][-150:] == pieces[1][:150]
    assert event("token", {"text": "hi"}) == 'event: token\ndata: {"text": "hi"}\n\n'


def test_tools_require_explicit_current_user_request() -> None:
    """RAG questions must not expose unrelated MCP tools to the model."""
    tools = [
        {"function": {"name": "create_file"}},
        {"function": {"name": "list_files"}},
        {"function": {"name": "read_file"}},
        {"function": {"name": "crawl_webpage"}},
        {"function": {"name": "get_weather"}},
    ]
    assert available_tools(tools, "hươu cao cổ là gì?") == []
    assert available_tools(tools, "Who is Ennov?") == []
    assert available_tools(tools, "What is the weather in Hanoi?") == tools[4:]
    assert available_tools(tools, "Browse the Ennov website") == tools[3:4]
    assert available_tools(tools, "Summarize https://en.ennov.com/") == tools[3:4]
    assert (
        available_tools(tools, "Open this URL https://example.com then summarize it")
        == tools[3:4]
    )
    assert available_tools(tools, "Open this URL then answer my question") == tools[3:4]
    vietnamese_request = (
        "mở url này https://vnexpress.net/ha-noi-tang-gia-trong-giu-oto-xe-may-5132893.html "
        "và tóm tắt nội dung cho tôi"
    )
    assert available_tools(tools, vietnamese_request) == tools[3:4]
    assert requested_web_url(vietnamese_request) == (
        "https://vnexpress.net/ha-noi-tang-gia-trong-giu-oto-xe-may-5132893.html"
    )
    assert (
        available_tools(tools, "Ouvrez https://example.com et résumez-le") == tools[3:4]
    )
    assert requested_web_url("Ouvrez https://example.com et résumez-le") is None
    assert available_tools(tools, "Read notes.txt") == tools[2:3]
    assert available_tools(tools, "List workspace files") == tools[1:2]
    assert available_tools(tools, "Create notes.txt") == tools[:1]
    assert requested_web_url(
        "Open this URL https://example.com/page then summarize it"
    ) == ("https://example.com/page")
    assert requested_web_url("Open https://example.com/page, then list key points") == (
        "https://example.com/page"
    )
    assert requested_web_url("hươu cao cổ là gì?") is None


def test_mcp_tools_roundtrip() -> None:
    """Discover the configured MCP tools and call a read-only tool."""

    async def check() -> None:
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
