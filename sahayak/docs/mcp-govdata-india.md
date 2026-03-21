# govdata-india MCP Server

## Overview

The `govdata-india` MCP server provides access to Indian government data APIs. It wraps four data sources behind MCP tools that the Sahayak agent can call to answer citizen queries about agricultural prices, government scheme benefits, weather, and PM-KISAN status.

## Tools

### `mandi_prices`

Fetches latest agricultural commodity prices from Agmarknet via data.gov.in.

**Input Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `commodity` | string | Yes | Crop name — "wheat", "rice", "tomato", "onion", etc. |
| `state` | string | No | State filter — "Madhya Pradesh", "Uttar Pradesh", etc. |
| `district` | string | No | District filter — "Bhopal", "Lucknow", etc. |

**Output:**
```json
{
  "prices": [
    {
      "mandi": "Bhopal",
      "commodity": "Wheat",
      "variety": "Lokwan",
      "min_price": 2000.0,
      "max_price": 2200.0,
      "modal_price": 2100.0,
      "date": "21/03/2026"
    }
  ],
  "source": "data.gov.in (Agmarknet)"
}
```

**Data Source:** `api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070`
**Cache TTL:** 6 hours (prices update daily)

**Data Flow:**
```
mandi_prices(commodity, state?, district?)
  → Check TTL cache (key: commodity:state:district)
  → If miss: GET api.data.gov.in with filters
  → Parse records into MandiPrice models
  → Cache result for 6h
  → Return MandiPricesResponse
```

---

### `pm_kisan_status`

Checks PM-KISAN (Pradhan Mantri Kisan Samman Nidhi) beneficiary data for a given state and district.

**Input Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | string | Yes | State name |
| `district` | string | Yes | District name |
| `block` | string | No | Block name for finer granularity |

**Output:**
```json
{
  "status": {
    "state": "Madhya Pradesh",
    "district": "Bhopal",
    "beneficiary_count": 15000,
    "last_installment": "17th",
    "amount_per_installment": 2000.0
  },
  "message": "",
  "source": "data.gov.in (PM-KISAN)"
}
```

**Data Source:** `api.data.gov.in/resource/a2dac80e-8e2c-4d0e-8194-5b498c9e24f3`
**Cache TTL:** 12 hours

**Data Flow:**
```
pm_kisan_status(state, district, block?)
  → Check TTL cache
  → If miss: GET api.data.gov.in with state/district/block filters
  → Parse first record into PMKisanStatus
  → Cache result for 12h
  → Return PMKisanResponse
```

---

### `weather_info`

Fetches current weather data and farming advisory for a district.

**Input Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `district` | string | Yes | District name |
| `state` | string | Yes | State name |

**Output:**
```json
{
  "weather": {
    "district": "Bhopal",
    "state": "Madhya Pradesh",
    "temp_max": 38.5,
    "temp_min": 22.0,
    "rainfall": 0.0,
    "humidity": 45.0,
    "forecast": "Clear sky",
    "advisory": "Suitable for sowing wheat"
  },
  "message": "",
  "source": "IMD / data.gov.in"
}
```

**Data Source:** `api.data.gov.in/resource/62bc2e75-6840-447e-8835-4f8f6fef2b4c`
**Cache TTL:** 3 hours

**Data Flow:**
```
weather_info(district, state)
  → Check TTL cache
  → If miss: GET api.data.gov.in with station=district filter
  → Parse into WeatherInfo (with safe_float for NA values)
  → Cache result for 3h
  → Return WeatherResponse
```

---

### `scheme_search`

Searches a curated database of 20 central government schemes. Fully offline — no API call needed.

**Input Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search keywords — "farmer pension", "housing", "girl child" |
| `age` | int | No | Beneficiary age for age-based filtering |
| `gender` | string | No | "male" or "female" |
| `category` | string | No | "sc", "st", "obc", "bpl", etc. |

**Output:**
```json
{
  "schemes": [
    {
      "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
      "ministry": "Ministry of Agriculture & Farmers Welfare",
      "benefits": "₹6,000 per year in 3 installments...",
      "eligibility": "All landholding farmer families...",
      "how_to_apply": "Apply at pmkisan.gov.in or visit nearest CSC...",
      "url": "https://pmkisan.gov.in"
    }
  ],
  "query": "farmer",
  "source": "Sahayak curated database"
}
```

**Data Source:** `sahayak/govdata-india/govdata_india/data/schemes.json`
**Cache:** None needed (static JSON loaded once at startup)

**Filtering Logic:**
1. Tokenize query and match against `name + benefits + eligibility` (case-insensitive)
2. If `gender` specified, filter by `gender_filter` field
3. If `category` specified, filter by `category_filter` field
4. If `age` specified, filter by `min_age` ≤ age ≤ `max_age`

**Schemes Included (20 total):**
- PM-KISAN, PMFBY (crop insurance), PM Kisan Maandhan (pension)
- Soil Health Card, PM Ujjwala (LPG), Ayushman Bharat (health insurance)
- PMAY-G and PMAY-U (housing), MGNREGA (employment guarantee)
- NSAP Old Age Pension, Sukanya Samriddhi (girl child savings)
- PM Mudra, Stand-Up India, PM Vishwakarma (enterprise loans)
- Atal Pension, PM Jan Dhan (banking), PM SHRI Schools
- PM Suraksha Bima, PM Jeevan Jyoti Bima (insurance)
- CSC (Common Service Centres)

---

## Caching Strategy

All API-backed tools use a `TTLCache` (time-to-live cache) — a simple dict with per-key expiry timestamps.

```python
class TTLCache:
    def get(key) → value | None   # Returns None if expired
    def set(key, value, ttl)      # Stores with expiry
    def clear()                    # Flush all entries
```

| Tool | TTL | Rationale |
|------|-----|-----------|
| `mandi_prices` | 6 hours | Prices update daily |
| `pm_kisan_status` | 12 hours | Installment data changes monthly |
| `weather_info` | 3 hours | Weather changes throughout the day |
| `scheme_search` | N/A | Static JSON, loaded once |

Cache is in-memory only — restarts flush it. This is acceptable for a demo; production would use Redis.

---

## Error Handling

All tools return structured responses, never raise exceptions to the MCP caller. This lets the LLM agent reason about failures:

```json
{
  "prices": [],
  "source": "data.gov.in (Agmarknet) — error: 500 Internal Server Error"
}
```

- HTTP errors → empty results + error message in `source` or `message` field
- Parse errors → skip individual records, return what parsed successfully
- Timeout → 10-second httpx timeout on all data.gov.in calls

---

## Authentication

Single env var: `DATA_GOV_IN_API_KEY`
- Free registration at [data.gov.in](https://data.gov.in)
- Passed as `api-key` query parameter on all requests
- If missing, requests may fail or return limited data

---

## Running

```bash
# Install
cd sahayak/govdata-india
pip install -e ".[dev]"

# Run as MCP server (stdio)
python -m govdata_india.server

# Run tests
python -m pytest tests/ -v
```
