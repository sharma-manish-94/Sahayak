"""Mandi (agricultural market) price lookup via data.gov.in Agmarknet API."""

from __future__ import annotations

import os
import httpx

from .cache import TTLCache
from .types import MandiPrice, MandiPricesResponse

_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
_BASE_URL = "https://api.data.gov.in/resource"
_MANDI_TTL = 6 * 3600  # 6 hours

_cache = TTLCache(default_ttl=_MANDI_TTL)


async def get_mandi_prices(
    commodity: str,
    state: str | None = None,
    district: str | None = None,
) -> MandiPricesResponse:
    """Fetch latest mandi prices for a commodity from Agmarknet via data.gov.in."""
    cache_key = f"mandi:{commodity}:{state}:{district}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    api_key = os.environ.get("DATA_GOV_IN_API_KEY", "")
    params: dict[str, str] = {
        "api-key": api_key,
        "format": "json",
        "limit": "20",
        "filters[commodity]": commodity.title(),
    }
    if state:
        params["filters[state]"] = state.title()
    if district:
        params["filters[district]"] = district.title()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{_BASE_URL}/{_RESOURCE_ID}", params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, Exception) as exc:
        return MandiPricesResponse(
            prices=[],
            source=f"data.gov.in (Agmarknet) — error: {exc}",
        )

    records = data.get("records", [])
    prices = []
    for r in records:
        try:
            prices.append(MandiPrice(
                mandi=r.get("market", ""),
                commodity=r.get("commodity", commodity),
                variety=r.get("variety", ""),
                min_price=float(r.get("min_price", 0)),
                max_price=float(r.get("max_price", 0)),
                modal_price=float(r.get("modal_price", 0)),
                date=r.get("arrival_date", ""),
            ))
        except (ValueError, TypeError):
            continue

    result = MandiPricesResponse(prices=prices)
    _cache.set(cache_key, result)
    return result
