"""Weather and agricultural advisory via data.gov.in / IMD."""

from __future__ import annotations

import os
import httpx

from .cache import TTLCache, fetch_with_retry
from .types import WeatherInfo, WeatherResponse

_RESOURCE_ID = "62bc2e75-6840-447e-8835-4f8f6fef2b4c"
_BASE_URL = "https://api.data.gov.in/resource"
_WEATHER_TTL = 3 * 3600  # 3 hours

_cache = TTLCache(default_ttl=_WEATHER_TTL)


async def get_weather(
    district: str,
    state: str,
) -> WeatherResponse:
    """Fetch weather data and farming advisory for a district."""
    cache_key = f"weather:{state}:{district}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    api_key = os.environ.get("DATA_GOV_IN_API_KEY", "")
    params: dict[str, str] = {
        "api-key": api_key,
        "format": "json",
        "limit": "5",
        "filters[station]": district.title(),
    }

    try:
        data = await fetch_with_retry(f"{_BASE_URL}/{_RESOURCE_ID}", params)
    except (httpx.HTTPError, Exception) as exc:
        return WeatherResponse(message=f"Error fetching weather data: {exc}")

    records = data.get("records", [])
    if not records:
        return WeatherResponse(message=f"No weather data found for {district}, {state}")

    r = records[0]

    def safe_float(val: str | None) -> float | None:
        if val is None or val == "" or val == "NA":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    weather = WeatherInfo(
        district=district,
        state=state,
        temp_max=safe_float(r.get("max_temp")),
        temp_min=safe_float(r.get("min_temp")),
        rainfall=safe_float(r.get("rainfall")),
        humidity=safe_float(r.get("humidity")),
        forecast=r.get("forecast", ""),
        advisory=r.get("advisory", ""),
    )

    result = WeatherResponse(weather=weather)
    _cache.set(cache_key, result)
    return result
