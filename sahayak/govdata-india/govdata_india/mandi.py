"""Mandi (agricultural market) price lookup via data.gov.in Agmarknet API."""

from __future__ import annotations

import os
import httpx

from .cache import TTLCache, fetch_with_retry
from .types import MandiPrice, MandiPricesResponse

_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
_BASE_URL = "https://api.data.gov.in/resource"
_MANDI_TTL = 6 * 3600  # 6 hours

# Common commodity names for fuzzy matching
_KNOWN_COMMODITIES = [
    "Wheat", "Rice", "Maize", "Cotton", "Soyabean", "Onion", "Potato",
    "Tomato", "Jowar", "Bajra", "Barley", "Groundnut", "Mustard",
    "Sugarcane", "Turmeric", "Chilli", "Garlic", "Ginger", "Brinjal",
    "Cauliflower", "Cabbage", "Green Peas", "Banana", "Mango", "Apple",
    "Gram", "Arhar", "Moong", "Urad", "Masoor", "Coriander", "Cumin",
]

_cache = TTLCache(default_ttl=_MANDI_TTL)


def _fuzzy_match_commodity(name: str) -> tuple[str, list[str]]:
    """Match commodity name loosely. Returns (best_match, suggestions)."""
    title = name.title()
    # Exact match
    if title in _KNOWN_COMMODITIES:
        return title, []
    # Substring / prefix match
    matches = [c for c in _KNOWN_COMMODITIES if title in c or c in title]
    if matches:
        return matches[0], matches[1:3]
    # Character-overlap similarity (simple Jaccard on trigrams)
    def trigrams(s: str) -> set[str]:
        s = s.lower()
        return {s[i:i + 3] for i in range(max(1, len(s) - 2))}
    query_tri = trigrams(name)
    scored = []
    for c in _KNOWN_COMMODITIES:
        c_tri = trigrams(c)
        if not query_tri or not c_tri:
            continue
        score = len(query_tri & c_tri) / len(query_tri | c_tri)
        if score > 0.2:
            scored.append((score, c))
    scored.sort(reverse=True)
    if scored:
        return scored[0][1], [s[1] for s in scored[1:4]]
    return title, []


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

    matched_commodity, suggestions = _fuzzy_match_commodity(commodity)

    api_key = os.environ.get("DATA_GOV_IN_API_KEY", "")
    params: dict[str, str] = {
        "api-key": api_key,
        "format": "json",
        "limit": "20",
        "filters[commodity]": matched_commodity,
    }
    if state:
        params["filters[state]"] = state.title()
    if district:
        params["filters[district]"] = district.title()

    try:
        data = await fetch_with_retry(f"{_BASE_URL}/{_RESOURCE_ID}", params)
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

    source = "data.gov.in (Agmarknet)"
    if not prices and suggestions:
        source += f" — no results for '{commodity}'. Try: {', '.join(suggestions)}"
    elif not prices and matched_commodity != commodity.title():
        source += f" — searched as '{matched_commodity}' (no results)"

    result = MandiPricesResponse(prices=prices, source=source)
    if prices:
        _cache.set(cache_key, result)
    return result
