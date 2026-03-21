"""PM-KISAN beneficiary status lookup via data.gov.in."""

from __future__ import annotations

import os
import httpx

from .cache import TTLCache
from .types import PMKisanStatus, PMKisanResponse

_RESOURCE_ID = "a2dac80e-8e2c-4d0e-8194-5b498c9e24f3"
_BASE_URL = "https://api.data.gov.in/resource"
_PMKISAN_TTL = 12 * 3600  # 12 hours

_cache = TTLCache(default_ttl=_PMKISAN_TTL)


async def get_pm_kisan_status(
    state: str,
    district: str,
    block: str | None = None,
) -> PMKisanResponse:
    """Fetch PM-KISAN beneficiary data for a state/district."""
    cache_key = f"pmkisan:{state}:{district}:{block}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    api_key = os.environ.get("DATA_GOV_IN_API_KEY", "")
    params: dict[str, str] = {
        "api-key": api_key,
        "format": "json",
        "limit": "5",
        "filters[state_name]": state.title(),
        "filters[district_name]": district.title(),
    }
    if block:
        params["filters[block_name]"] = block.title()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{_BASE_URL}/{_RESOURCE_ID}", params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, Exception) as exc:
        return PMKisanResponse(message=f"Error fetching PM-KISAN data: {exc}")

    records = data.get("records", [])
    if not records:
        return PMKisanResponse(message=f"No PM-KISAN data found for {district}, {state}")

    # Aggregate from available records
    r = records[0]
    try:
        status = PMKisanStatus(
            state=r.get("state_name", state),
            district=r.get("district_name", district),
            beneficiary_count=int(r.get("registered_farmer", 0)),
            last_installment=r.get("instalment", "N/A"),
            amount_per_installment=2000.0,
        )
    except (ValueError, TypeError):
        return PMKisanResponse(message="Error parsing PM-KISAN data")

    result = PMKisanResponse(status=status)
    _cache.set(cache_key, result)
    return result
