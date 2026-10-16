"""Core chat and MCP behavior checks."""

from app.features.chat.orchestrator import event
from app.features.rag.service import chunks


def test_chunk_overlap_and_stream_format() -> None:
    """Preserve chunk overlap and SSE serialization."""
    pieces = chunks("a" * 1300)
    assert len(pieces) == 2
    assert pieces[0][-150:] == pieces[1][:150]
    assert event("token", {"text": "hi"}) == 'event: token\ndata: {"text": "hi"}\n\n'
