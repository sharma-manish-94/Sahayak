"""Tests for govdata-india MCP server tools."""

from __future__ import annotations

import json
import pytest
import httpx
import respx

from govdata_india.server import mcp
from govdata_india.schemes import search_schemes


# --- Scheme search (offline, no mocking needed) ---

class TestSchemeSearch:
    def test_search_by_keyword(self):
        result = search_schemes("farmer")
        assert len(result.schemes) > 0
        names = [s.name for s in result.schemes]
        assert any("KISAN" in n or "Kisan" in n for n in names)

    def test_search_pension(self):
        result = search_schemes("pension")
        assert len(result.schemes) > 0

    def test_search_with_gender_filter(self):
        result = search_schemes("yojana", gender="female")
        assert len(result.schemes) > 0

    def test_search_with_age_filter(self):
        result = search_schemes("pension", age=25)
        for scheme in result.schemes:
            # All returned schemes should be valid for age 25
            assert scheme.name  # basic validation

    def test_search_no_results(self):
        result = search_schemes("xyznonexistent12345")
        assert len(result.schemes) == 0

    def test_search_housing(self):
        result = search_schemes("Awas")
        assert len(result.schemes) > 0
        names = [s.name for s in result.schemes]
        assert any("Awas" in n for n in names)


# --- Mandi prices (mocked HTTP) ---

class TestMandiPrices:
    @pytest.mark.asyncio
    @respx.mock
    async def test_mandi_prices_success(self, mock_api_key):
        from govdata_india.mandi import get_mandi_prices, _cache
        _cache.clear()

        respx.get("https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070").mock(
            return_value=httpx.Response(200, json={
                "records": [
                    {
                        "market": "Bhopal",
                        "commodity": "Wheat",
                        "variety": "Lokwan",
                        "min_price": "2000",
                        "max_price": "2200",
                        "modal_price": "2100",
                        "arrival_date": "21/03/2026",
                    }
                ]
            })
        )

        result = await get_mandi_prices("wheat", state="Madhya Pradesh")
        assert len(result.prices) == 1
        assert result.prices[0].mandi == "Bhopal"
        assert result.prices[0].modal_price == 2100.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_mandi_prices_api_error(self, mock_api_key):
        from govdata_india.mandi import get_mandi_prices, _cache
        _cache.clear()

        respx.get("https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070").mock(
            return_value=httpx.Response(500)
        )

        result = await get_mandi_prices("wheat")
        assert len(result.prices) == 0
        assert "error" in result.source


# --- PM-KISAN (mocked HTTP) ---

class TestPMKisan:
    @pytest.mark.asyncio
    @respx.mock
    async def test_pm_kisan_success(self, mock_api_key):
        from govdata_india.pmkisan import get_pm_kisan_status, _cache
        _cache.clear()

        respx.get("https://api.data.gov.in/resource/a2dac80e-8e2c-4d0e-8194-5b498c9e24f3").mock(
            return_value=httpx.Response(200, json={
                "records": [
                    {
                        "state_name": "Madhya Pradesh",
                        "district_name": "Bhopal",
                        "registered_farmer": "15000",
                        "instalment": "17th",
                    }
                ]
            })
        )

        result = await get_pm_kisan_status("Madhya Pradesh", "Bhopal")
        assert result.status is not None
        assert result.status.beneficiary_count == 15000

    @pytest.mark.asyncio
    @respx.mock
    async def test_pm_kisan_no_data(self, mock_api_key):
        from govdata_india.pmkisan import get_pm_kisan_status, _cache
        _cache.clear()

        respx.get("https://api.data.gov.in/resource/a2dac80e-8e2c-4d0e-8194-5b498c9e24f3").mock(
            return_value=httpx.Response(200, json={"records": []})
        )

        result = await get_pm_kisan_status("Unknown", "Unknown")
        assert result.status is None
        assert "No PM-KISAN data" in result.message


# --- Weather (mocked HTTP) ---

class TestWeather:
    @pytest.mark.asyncio
    @respx.mock
    async def test_weather_success(self, mock_api_key):
        from govdata_india.weather import get_weather, _cache
        _cache.clear()

        respx.get("https://api.data.gov.in/resource/62bc2e75-6840-447e-8835-4f8f6fef2b4c").mock(
            return_value=httpx.Response(200, json={
                "records": [
                    {
                        "max_temp": "38.5",
                        "min_temp": "22.0",
                        "rainfall": "0.0",
                        "humidity": "45",
                        "forecast": "Clear sky",
                        "advisory": "Suitable for sowing wheat",
                    }
                ]
            })
        )

        result = await get_weather("Bhopal", "Madhya Pradesh")
        assert result.weather is not None
        assert result.weather.temp_max == 38.5
        assert result.weather.forecast == "Clear sky"
