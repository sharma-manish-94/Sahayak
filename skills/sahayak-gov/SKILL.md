---
name: sahayak-gov
description: Indian government data APIs — mandi prices, PM-KISAN beneficiary status, weather advisories, scheme search
mcp_server: govdata-india
---

# Sahayak Government Data Services

This skill provides access to Indian government data APIs for citizen services.

## Tools

### mandi_prices
Get latest agricultural mandi (market) prices for a commodity.
- Source: data.gov.in Agmarknet
- Cached for 6 hours
- Filter by commodity (required), state, and district
- Example: mandi_prices(commodity="wheat", state="Madhya Pradesh", district="Bhopal")

### pm_kisan_status
Check PM-KISAN beneficiary data for a state/district.
- Source: data.gov.in PM-KISAN dataset
- Returns beneficiary count, last installment info
- Example: pm_kisan_status(state="Madhya Pradesh", district="Bhopal")

### weather_info
Get current weather and farming advisory for a district.
- Source: IMD data via data.gov.in
- Cached for 3 hours
- Returns temperature, rainfall, humidity, forecast, advisory
- Example: weather_info(district="Bhopal", state="Madhya Pradesh")

### scheme_search
Search curated database of 20 central government schemes.
- Offline search — no API call needed
- Filter by keyword, age, gender, category (SC/ST/BPL)
- Example: scheme_search(query="farmer pension", age=35)

## When to use
- User asks about crop/mandi prices → mandi_prices
- User asks about PM-KISAN status/money → pm_kisan_status
- User asks about weather/farming advice → weather_info
- User asks about government schemes/yojana → scheme_search
- For compound queries, combine multiple tools
