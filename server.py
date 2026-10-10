"""
server.py — MCP server that exposes file-management and weather tools.

Run directly:       python server.py          (listens on stdio)
Debug with Inspector: npx @modelcontextprotocol/inspector python server.py

Architecture:
  The server is a long-running process launched by the *client* as a subprocess.
  Communication happens over stdin/stdout using the MCP protocol (JSON-RPC).
  The MCPServer class (from the `mcp` SDK v2) handles all the protocol plumbing;
  we just decorate plain Python functions with @mcp.tool(), @mcp.resource(), etc.
"""

from html.parser import HTMLParser
from pathlib import Path
import re

import httpx

# --- MCP SDK v2 imports ---
# In v2 the high-level class was renamed from FastMCP → MCPServer.
# If you are on mcp <2.0, use: from mcp.server.fastmcp import FastMCP
from mcp.server.mcpserver import MCPServer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# All file operations are sandboxed to this directory.
WORKSPACE = Path(__file__).parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)

# Regex for safe filenames: letters, digits, underscores, hyphens, one dot.
SAFE_NAME = re.compile(r"^[\w\-]+(\.[\w\-]+)?$")

# Timeout for external HTTP calls (seconds).
HTTP_TIMEOUT = 10.0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_path(filename: str) -> Path:
    """
    Resolve `filename` inside WORKSPACE and reject anything suspicious.
    Raises ValueError on invalid names (path traversal, absolute paths, etc.).
    """
    # Block absolute paths, directory traversal, and subdirectory separators.
    if not SAFE_NAME.match(filename):
        raise ValueError(
            f"Invalid filename: {filename!r}. "
            "Use only letters, digits, underscores, hyphens, and a single dot."
        )
    resolved = (WORKSPACE / filename).resolve()
    # Double-check the resolved path is still inside the workspace.
    if not str(resolved).startswith(str(WORKSPACE.resolve())):
        raise ValueError("Path escapes the workspace directory.")
    return resolved


# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------

# The name appears in MCP Inspector and client logs.
mcp = MCPServer("learning-tools")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def create_file(filename: str, content: str = "") -> str:
    """
    Create a new file in the workspace directory.

    Args:
        filename: Name of the file to create (e.g. "notes.txt").
                  Must be a simple name — no paths, no ".." allowed.
        content:  Optional text to write into the file. Defaults to empty.

    Returns:
        A success message with the file path, or an error if the file
        already exists.
    """
    try:
        path = _safe_path(filename)
    except ValueError as e:
        return f"Error: {e}"

    if path.exists():
        return f"Error: file '{filename}' already exists. Will not overwrite."

    path.write_text(content, encoding="utf-8")
    return f"Created file: {path.name} ({len(content)} bytes)"


@mcp.tool()
def list_files() -> str:
    """
    List all files in the workspace directory.

    Returns:
        A newline-separated list of filenames, or a message if the
        workspace is empty.
    """
    files = sorted(f.name for f in WORKSPACE.iterdir() if f.is_file())
    if not files:
        return "The workspace is empty — no files yet."
    return "Files in workspace:\n" + "\n".join(f"  • {f}" for f in files)


@mcp.tool()
def read_file(filename: str) -> str:
    """
    Read the contents of a file in the workspace directory.

    Args:
        filename: Name of the file to read.

    Returns:
        The file contents, or an error message if the file does not exist.
    """
    try:
        path = _safe_path(filename)
    except ValueError as e:
        return f"Error: {e}"

    if not path.exists():
        return f"Error: file '{filename}' not found in the workspace."
    return path.read_text(encoding="utf-8")


@mcp.tool()
async def get_weather(city: str) -> str:
    """
    Get the current weather for a city using the free Open-Meteo API.

    Steps: geocode the city name → fetch current weather → return a summary.
    No API key is required.

    Args:
        city: Name of the city (e.g. "Hanoi", "London").

    Returns:
        A short human-readable weather summary, or an error message.
    """
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            # Step 1: Geocode the city name to latitude/longitude.
            geo_resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1},
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

            results = geo_data.get("results")
            if not results:
                return f"City '{city}' not found. Try a different spelling."

            loc = results[0]
            lat, lon = loc["latitude"], loc["longitude"]
            display_name = f"{loc['name']}, {loc.get('country', '')}"

            # Step 2: Fetch current weather using coordinates.
            wx_resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": ["temperature_2m", "wind_speed_10m",
                                "relative_humidity_2m", "weather_code"],
                },
            )
            wx_resp.raise_for_status()
            current = wx_resp.json()["current"]

            temp = current["temperature_2m"]
            wind = current["wind_speed_10m"]
            humidity = current["relative_humidity_2m"]

            return (
                f"Weather in {display_name}:\n"
                f"  Temperature: {temp} °C\n"
                f"  Wind speed:  {wind} km/h\n"
                f"  Humidity:    {humidity}%"
            )

    except httpx.HTTPStatusError as e:
        return f"HTTP error from Open-Meteo: {e.response.status_code}"
    except httpx.RequestError as e:
        return f"Network error: {e}"


# ---------------------------------------------------------------------------
# HTML text cleaner for the web crawler tool
# ---------------------------------------------------------------------------

class HTMLTextCleaner(HTMLParser):
    """Simple parser to strip scripts/styles and extract readable text from HTML."""
    def __init__(self):
        super().__init__()
        self.text_chunks = []
        self._ignore = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg", "header", "footer", "nav"):
            self._ignore = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg", "header", "footer", "nav"):
            self._ignore = False
        elif tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br", "tr"):
            self.text_chunks.append("\n")

    def handle_data(self, data):
        if not self._ignore:
            cleaned = data.strip()
            if cleaned:
                self.text_chunks.append(cleaned + " ")

    def get_clean_text(self) -> str:
        raw = "".join(self.text_chunks)
        lines = [line.strip() for line in raw.split("\n")]
        return "\n".join(line for line in lines if line)


@mcp.tool()
async def crawl_webpage(url: str) -> str:
    """
    Crawl and extract readable text from a web page URL.
    Use this tool when the user asks about an entity, company, or topic and a website
    link/URL is available in the context or request to fetch up-to-date information.

    Args:
        url: Full web URL to fetch (e.g. "https://en.ennov.com/").

    Returns:
        Extracted text content from the webpage, trimmed for prompt length,
        or an error message if fetching fails.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        return f"Error: Invalid URL '{url}'. Must start with http:// or https://"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True, headers=headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            parser = HTMLTextCleaner()
            parser.feed(resp.text)
            text = parser.get_clean_text()

            if not text:
                return f"Fetched {url}, but found no readable text."

            # Trim to ~3000 chars to avoid overflowing model context
            trimmed_text = text[:3000]
            if len(text) > 3000:
                trimmed_text += "\n\n...[Content truncated for length]..."

            return f"--- Content crawled from {url} ---\n{trimmed_text}"

    except httpx.HTTPStatusError as e:
        return f"HTTP error while crawling {url}: {e.response.status_code}"
    except httpx.RequestError as e:
        return f"Network error while crawling {url}: {e}"


# ---------------------------------------------------------------------------
# [Optional] MCP Resource — demonstrates the "resource" primitive.
# Resources are read-only data the server can expose (like a GET endpoint).
# ---------------------------------------------------------------------------

@mcp.resource("docs://list")
def list_docs() -> str:
    """List the RAG document filenames available in the data/ directory."""
    data_dir = Path(__file__).parent / "data"
    files = sorted(f.name for f in data_dir.glob("*.txt"))
    return "Available RAG documents:\n" + "\n".join(f"  • {f}" for f in files)


# ---------------------------------------------------------------------------
# [Optional] MCP Prompt — demonstrates the "prompt" primitive.
# Prompts are reusable message templates the server can suggest to clients.
# ---------------------------------------------------------------------------

@mcp.prompt()
def summarize_file(filename: str) -> str:
    """
    Prompt template: ask the LLM to summarize a workspace file.

    Args:
        filename: The file to summarize.
    """
    return f"Please read the file '{filename}' from the workspace and provide a concise summary of its contents."


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # mcp.run() starts the server on stdio transport by default.
    # The client will launch this script as a subprocess.
    mcp.run()
