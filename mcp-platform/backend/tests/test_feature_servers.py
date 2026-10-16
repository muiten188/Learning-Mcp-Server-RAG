"""Feature MCP server checks using local API responses."""

import asyncio
import runpy
from pathlib import Path
from unittest.mock import patch

import httpx

SERVER_ROOT = Path(__file__).resolve().parents[2] / "mcp_servers"


def test_database_server_lists_registered_tables() -> None:
    """Read table metadata from SQLAlchemy rather than a fixed list."""
    database_tables = runpy.run_path(str(SERVER_ROOT / "database" / "server.py"))[
        "database_tables"
    ]
    tables = asyncio.run(database_tables())
    assert "conversations" in tables
    assert "document_chunks" in tables


def test_weather_server_formats_three_day_forecast() -> None:
    """Parse and format Open-Meteo responses without a network request."""

    def respond(request: httpx.Request) -> httpx.Response:
        if "geocoding-api" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Hanoi",
                            "country": "Vietnam",
                            "latitude": 21.0,
                            "longitude": 105.8,
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "daily": {
                    "time": ["2026-10-17", "2026-10-18", "2026-10-19"],
                    "temperature_2m_min": [22, 23, 24],
                    "temperature_2m_max": [30, 31, 32],
                }
            },
        )

    get_forecast = runpy.run_path(str(SERVER_ROOT / "weather" / "server.py"))[
        "get_forecast"
    ]
    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    with patch.object(httpx, "AsyncClient", return_value=client):
        result = asyncio.run(get_forecast("Hanoi"))
    assert result.splitlines() == [
        "2026-10-17: 22.0–30.0 °C",
        "2026-10-18: 23.0–31.0 °C",
        "2026-10-19: 24.0–32.0 °C",
    ]
