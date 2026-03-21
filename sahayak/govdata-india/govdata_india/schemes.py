"""Scheme search — offline JSON-based lookup."""

from __future__ import annotations

import json
from pathlib import Path

from .types import Scheme, SchemesResponse

_SCHEMES_PATH = Path(__file__).parent / "data" / "schemes.json"
_schemes: list[dict] | None = None


def _load_schemes() -> list[dict]:
    global _schemes
    if _schemes is None:
        _schemes = json.loads(_SCHEMES_PATH.read_text(encoding="utf-8"))
    return _schemes


def search_schemes(
    query: str,
    age: int | None = None,
    gender: str | None = None,
    category: str | None = None,
) -> SchemesResponse:
    """Search curated central government schemes by keyword and optional filters."""
    schemes = _load_schemes()
    query_lower = query.lower()
    results: list[Scheme] = []

    for s in schemes:
        # Keyword match against name, benefits, eligibility
        searchable = f"{s['name']} {s['benefits']} {s['eligibility']}".lower()
        if not any(tok in searchable for tok in query_lower.split()):
            continue

        # Optional filters
        if gender and s.get("gender_filter") and gender.lower() not in s["gender_filter"].lower():
            continue
        if category and s.get("category_filter") and category.lower() not in s["category_filter"].lower():
            continue
        if age is not None:
            min_age = s.get("min_age", 0)
            max_age = s.get("max_age", 200)
            if not (min_age <= age <= max_age):
                continue

        results.append(Scheme(
            name=s["name"],
            ministry=s["ministry"],
            benefits=s["benefits"],
            eligibility=s["eligibility"],
            how_to_apply=s["how_to_apply"],
            url=s.get("url", ""),
        ))

    return SchemesResponse(schemes=results, query=query)
