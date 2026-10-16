"""MCP tools for current weather and short forecasts."""

import os

import httpx
from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field

mcp = MCPServer("weather")


class Location(BaseModel):
    """Coordinates returned by Open-Meteo geocoding."""

    name: str
    country: str = ""
    latitude: float
    longitude: float


class Locations(BaseModel):
    """Open-Meteo geocoding matches."""

    results: list[Location] = Field(default_factory=list)


class CurrentWeather(BaseModel):
    """Current Open-Meteo weather observations."""

    temperature_2m: float
    wind_speed_10m: float
    relative_humidity_2m: float


class WeatherResponse(BaseModel):
    """Open-Meteo current-weather response."""

    current: CurrentWeather


class DailyForecast(BaseModel):
    """Daily forecast values returned by Open-Meteo."""

    time: list[str]
    temperature_2m_max: list[float]
    temperature_2m_min: list[float]


class ForecastResponse(BaseModel):
    """Open-Meteo forecast response."""

    daily: DailyForecast


async def _location(client: httpx.AsyncClient, city: str) -> Location | None:
    response = await client.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
    )
    response.raise_for_status()
    matches = Locations.model_validate(response.json()).results
    return matches[0] if matches else None


@mcp.tool()
async def get_weather(city: str) -> str:
    """Get current temperature, wind speed, and humidity for a city.

    Args:
        city: City named by the user.

    Returns:
        Human-readable current conditions or an error message.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            location = await _location(client, city)
            if location is None:
                return f"City '{city}' not found"
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "current": [
                        "temperature_2m",
                        "wind_speed_10m",
                        "relative_humidity_2m",
                    ],
                },
            )
            response.raise_for_status()
            weather = WeatherResponse.model_validate(response.json()).current
            return (
                f"Weather in {location.name}, {location.country}: "
                f"{weather.temperature_2m} °C, wind {weather.wind_speed_10m} km/h, "
                f"humidity {weather.relative_humidity_2m}%"
            )
    except httpx.HTTPError as exc:
        return f"Weather service error: {exc}"


@mcp.tool()
async def get_forecast(city: str) -> str:
    """Get the next three days of high and low temperatures for a city.

    Args:
        city: City named by the user.

    Returns:
        Human-readable daily forecast or an error message.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            location = await _location(client, city)
            if location is None:
                return f"City '{city}' not found"
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "daily": ["temperature_2m_max", "temperature_2m_min"],
                    "forecast_days": 3,
                },
            )
            response.raise_for_status()
            daily = ForecastResponse.model_validate(response.json()).daily
            return "\n".join(
                f"{day}: {low}–{high} °C"
                for day, low, high in zip(
                    daily.time,
                    daily.temperature_2m_min,
                    daily.temperature_2m_max,
                    strict=True,
                )
            )
    except (httpx.HTTPError, ValueError) as exc:
        return f"Forecast service error: {exc}"


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(
            os.environ.get("MCP_WEATHER_PORT", os.environ.get("MCP_PORT", "8102"))
        ),
        stateless_http=True,
    )
