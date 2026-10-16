"""MCP tool for reading a requested webpage."""

import os
from html.parser import HTMLParser

import httpx
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("web")


class PageText(HTMLParser):
    """Collect readable HTML text while skipping script and style content."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Skip non-content elements and separate text blocks."""
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
        elif tag in {"p", "div", "li", "br", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        """Resume text collection after non-content elements."""
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        """Collect visible text nodes."""
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip() + " ")


@mcp.tool()
async def crawl_webpage(url: str) -> str:
    """Read one HTTP or HTTPS page explicitly requested by the user.

    Args:
        url: Exact page URL supplied by the user.

    Returns:
        Extracted page text or an error message.
    """
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
        parser = PageText()
        parser.feed(response.text)
        content = " ".join(" ".join(parser.parts).split())
        return (
            f"Content crawled from {url}:\n{content[:3000]}"
            if content
            else "No readable page text"
        )
    except httpx.HTTPError as exc:
        return f"Error reading {url}: {exc}"


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.environ.get("MCP_WEB_PORT", os.environ.get("MCP_PORT", "8105"))),
        stateless_http=True,
    )
