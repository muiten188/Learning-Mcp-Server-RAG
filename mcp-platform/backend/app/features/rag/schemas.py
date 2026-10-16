"""Named retrieval results shared by the RAG repository and chat service."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    """A document filename and the matching text chunk."""

    filename: str
    content: str
