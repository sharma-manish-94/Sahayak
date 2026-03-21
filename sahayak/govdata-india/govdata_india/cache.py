"""Generic TTL cache and shared HTTP helpers for data.gov.in API."""

from __future__ import annotations

import time
from typing import Any

import httpx

_MAX_RETRIES = 1


class TTLCache:
    """Simple dict-based cache with per-key expiry timestamps."""

    def __init__(self, default_ttl: float = 3600.0) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        ttl = ttl if ttl is not None else self._default_ttl
        self._store[key] = (time.monotonic() + ttl, value)

    def clear(self) -> None:
        self._store.clear()


async def fetch_with_retry(url: str, params: dict[str, str]) -> dict:
    """GET request with one retry on 5xx errors and 10s timeout."""
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code >= 500 and attempt < _MAX_RETRIES:
                    last_exc = httpx.HTTPStatusError(
                        f"Server error {resp.status_code}",
                        request=resp.request, response=resp,
                    )
                    continue
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError:
            raise
        except httpx.HTTPError as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                continue
            raise
    raise last_exc or httpx.HTTPError("Request failed after retries")
