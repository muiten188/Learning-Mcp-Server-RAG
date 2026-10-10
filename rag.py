"""
rag.py — Simple RAG (Retrieval-Augmented Generation) without embeddings or a vector DB.

Design decision: We use approach (b) — naive keyword matching.
  • Approach (a) "inject everything" is simpler but wastes context window on
    irrelevant documents. Fine for 3 tiny files, but doesn't teach retrieval.
  • Approach (b) scores each document by how many of the user's query words
    appear in it, then injects only the top-scoring document(s). This is still
    dead-simple but introduces the *concept* of retrieval, which is the whole
    point of RAG. The trade-off: keyword matching misses synonyms and semantics
    (e.g. "weather" won't match "climate"). Real RAG systems use embeddings to
    fix this, but that's a "what to try next" exercise.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Load documents
# ---------------------------------------------------------------------------

# DATA_DIR is relative to this file so the project works from any cwd.
DATA_DIR = Path(__file__).parent / "data"


def load_documents(data_dir: Path = DATA_DIR) -> dict[str, str]:
    """Read every .txt file in `data_dir` into a {filename: content} dict."""
    docs: dict[str, str] = {}
    for txt_file in sorted(data_dir.glob("*.txt")):
        docs[txt_file.name] = txt_file.read_text(encoding="utf-8")
    return docs


# ---------------------------------------------------------------------------
# 2. Retrieve relevant documents
# ---------------------------------------------------------------------------

def retrieve(query: str, docs: dict[str, str], top_k: int = 2) -> list[tuple[str, str]]:
    """
    Score each document by the number of query words it contains (case-insensitive),
    then return the top-k (filename, content) pairs.

    This is intentionally naive — it's here to illustrate the *retrieval* step
    of RAG. A real system would use vector similarity (e.g. cosine distance on
    embeddings) instead of raw word counts.
    """
    # Normalise the query into lowercase keywords without punctuation.
    # We strip short words (<=2 chars) to skip "is", "a", "to", etc.
    import re
    words = re.findall(r"[\w-]+", query.lower())
    query_words = {w for w in words if len(w) > 2}

    scored: list[tuple[int, str, str]] = []
    for filename, content in docs.items():
        content_lower = content.lower()
        # Count how many distinct query words appear anywhere in the document.
        score = sum(1 for w in query_words if w in content_lower)
        scored.append((score, filename, content))

    # Sort descending by score; take the top_k that scored > 0.
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(fname, content) for score, fname, content in scored[:top_k] if score > 0]


# ---------------------------------------------------------------------------
# 3. Format context for the system prompt
# ---------------------------------------------------------------------------

def build_context_block(query: str, docs: dict[str, str]) -> str:
    """
    Build a text block that can be appended to the system prompt to give the
    LLM relevant background knowledge.

    Returns an empty string when no documents match, so the caller can simply
    concatenate it without conditionals.
    """
    relevant = retrieve(query, docs)
    if not relevant:
        return ""

    sections = ["[Retrieved context — use this to answer the user's question]"]
    for fname, content in relevant:
        sections.append(f"--- {fname} ---\n{content}")
    sections.append("[End of retrieved context]")

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Quick self-test: run `python rag.py` to see retrieval in action.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents: {list(docs.keys())}\n")

    test_queries = ["What is MCP?", "Python tips", "contact support"]
    for q in test_queries:
        print(f"Query: {q!r}")
        for fname, _ in retrieve(q, docs):
            print(f"  → matched: {fname}")
        print()
