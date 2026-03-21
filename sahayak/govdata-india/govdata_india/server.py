"""govdata-india MCP server — exposes Indian government data tools."""

from __future__ import annotations

from fastmcp import FastMCP

from .mandi import get_mandi_prices
from .pmkisan import get_pm_kisan_status
from .weather import get_weather
from .schemes import search_schemes

mcp = FastMCP(
    "govdata-india",
    instructions="Indian government data APIs — mandi prices, PM-KISAN status, weather, scheme search",
)


@mcp.tool()
async def mandi_prices(
    commodity: str,
    state: str | None = None,
    district: str | None = None,
) -> dict:
    """Get latest agricultural mandi (market) prices for a commodity.

    Args:
        commodity: Crop name, e.g. "wheat", "rice", "tomato", "onion"
        state: Optional state filter, e.g. "Madhya Pradesh"
        district: Optional district filter, e.g. "Bhopal"
    """
    result = await get_mandi_prices(commodity, state, district)
    return result.model_dump()


@mcp.tool()
async def pm_kisan_status(
    state: str,
    district: str,
    block: str | None = None,
) -> dict:
    """Check PM-KISAN beneficiary status for a state/district.

    Args:
        state: State name, e.g. "Madhya Pradesh"
        district: District name, e.g. "Bhopal"
        block: Optional block name for more specific data
    """
    result = await get_pm_kisan_status(state, district, block)
    return result.model_dump()


@mcp.tool()
async def weather_info(
    district: str,
    state: str,
) -> dict:
    """Get current weather and farming advisory for a district.

    Args:
        district: District name, e.g. "Bhopal"
        state: State name, e.g. "Madhya Pradesh"
    """
    result = await get_weather(district, state)
    return result.model_dump()


@mcp.tool()
def scheme_search(
    query: str,
    age: int | None = None,
    gender: str | None = None,
    category: str | None = None,
) -> dict:
    """Search government welfare schemes by keyword and optional demographic filters.

    Args:
        query: Search keywords, e.g. "farmer pension", "housing", "girl child education"
        age: Optional age of the beneficiary for age-based filtering
        gender: Optional gender filter — "male" or "female"
        category: Optional category — "sc", "st", "obc", "bpl", etc.
    """
    result = search_schemes(query, age, gender, category)
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
