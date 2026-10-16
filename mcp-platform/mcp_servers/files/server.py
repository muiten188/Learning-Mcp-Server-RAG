"""MCP tools for the sandboxed application workspace."""

import os
import re
from pathlib import Path

from mcp.server.mcpserver import MCPServer

WORKSPACE = Path(
    os.environ.get(
        "MCP_WORKSPACE", str(Path(__file__).resolve().parents[2] / "workspace")
    )
)
SAFE_NAME = re.compile(r"^[\w-]+(?:\.[\w-]+)?$")
mcp = MCPServer("files")


def _safe_path(filename: str) -> Path:
    if not SAFE_NAME.fullmatch(filename):
        raise ValueError("Use a simple filename without directory separators")
    path = (WORKSPACE / filename).resolve()
    if path.parent != WORKSPACE.resolve():
        raise ValueError("Filename escapes the workspace")
    return path


@mcp.tool()
def create_file(filename: str, content: str = "") -> str:
    """Create a new UTF-8 workspace file when the user asks for it.

    Args:
        filename: Simple filename without a directory path.
        content: Text to save.

    Returns:
        Confirmation or a validation error. Existing files are not overwritten.
    """
    try:
        path = _safe_path(filename)
        WORKSPACE.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(content)
    except (ValueError, FileExistsError) as exc:
        return f"Error: {exc}"
    return f"Created file: {path.name} ({len(content)} bytes)"


@mcp.tool()
def list_files() -> str:
    """List filenames in the application workspace.

    Returns:
        Newline-separated filenames or an empty-workspace message.
    """
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    names = sorted(path.name for path in WORKSPACE.iterdir() if path.is_file())
    return (
        "Files in workspace:\n" + "\n".join(names)
        if names
        else "The workspace is empty"
    )


@mcp.tool()
def read_file(filename: str) -> str:
    """Read a named UTF-8 workspace file.

    Args:
        filename: Simple filename without a directory path.

    Returns:
        File contents or an error message.
    """
    try:
        return _safe_path(filename).read_text(encoding="utf-8")
    except (ValueError, OSError) as exc:
        return f"Error: {exc}"


@mcp.tool()
def search_files(query: str) -> str:
    """Find workspace filenames containing the requested text.

    Args:
        query: Case-insensitive filename fragment.

    Returns:
        Matching filenames or a no-match message.
    """
    if not query.strip():
        return "Error: Search query must not be empty"
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    names = sorted(
        path.name
        for path in WORKSPACE.iterdir()
        if path.is_file() and query.casefold() in path.name.casefold()
    )
    return "\n".join(names) if names else "No matching files"


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.environ.get("MCP_FILES_PORT", os.environ.get("MCP_PORT", "8101"))),
        stateless_http=True,
    )
