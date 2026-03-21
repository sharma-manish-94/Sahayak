# Local Debugging & Testing Guide

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.11+ | `python --version` |
| Node.js | 22+ | `node --version` |
| pnpm | 9+ | `pnpm --version` |
| pip | latest | `pip --version` |

## 1. Setting Up the Dev Environment

### Install MCP Server Dependencies

```bash
# govdata-india
cd sahayak/govdata-india
pip install -e ".[dev]"

# bhashini-lang
cd ../bhashini-lang
pip install -e ".[dev]"
```

The `-e` (editable) flag means changes to `.py` files take effect immediately — no reinstall needed.

### Environment Variables

Create a `.env` file at the repo root (or export in your shell):

```bash
# Required for govdata-india
DATA_GOV_IN_API_KEY=your_data_gov_key

# Required for bhashini-lang (skip if testing with fallbacks only)
BHASHINI_ULCA_USER_ID=your_user_id
BHASHINI_ULCA_API_KEY=your_api_key

# Required for Whisper fallback ASR
OPENAI_API_KEY=your_openai_key

# Required for the Sahayak agent
ANTHROPIC_API_KEY=your_anthropic_key
```

To get free API keys:
- **data.gov.in**: Register at https://data.gov.in → My Account → Generate API Key
- **Bhashini ULCA**: Register at https://bhashini.gov.in/ulca → free PoC tier
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys

---

## 2. Running Tests

### Unit Tests (Mocked HTTP — No API Keys Needed)

```bash
# govdata-india — 11 tests
cd sahayak/govdata-india
python -m pytest tests/ -v

# bhashini-lang — 6 tests
cd sahayak/bhashini-lang
python -m pytest tests/ -v
```

These tests use `respx` to mock all HTTP calls, so they run offline and don't need real API keys.

### Running a Single Test

```bash
# By test name
python -m pytest tests/test_server.py::TestSchemeSearch::test_search_by_keyword -v

# By keyword match
python -m pytest tests/ -k "mandi" -v

# By test class
python -m pytest tests/test_server.py::TestMandiPrices -v
```

### Running Tests with Debug Output

```bash
# Show print statements and full tracebacks
python -m pytest tests/ -v -s --tb=long

# Show local variables on failure
python -m pytest tests/ -v --tb=short -l
```

### Test Coverage

```bash
pip install pytest-cov

# Coverage for govdata-india
cd sahayak/govdata-india
python -m pytest tests/ --cov=govdata_india --cov-report=term-missing

# Coverage for bhashini-lang
cd sahayak/bhashini-lang
python -m pytest tests/ --cov=bhashini_lang --cov-report=term-missing
```

The `--cov-report=term-missing` flag shows exactly which lines are uncovered.

---

## 3. Testing Individual Components

### Scheme Search (Fully Offline)

The scheme search tool is the simplest to test — no API calls, no env vars:

```bash
cd sahayak/govdata-india
python -c "
from govdata_india.schemes import search_schemes

# Basic keyword search
result = search_schemes('farmer')
for s in result.schemes:
    print(f'  {s.name}: {s.benefits[:60]}...')

# With filters
result = search_schemes('pension', age=35)
print(f'\nPension schemes for age 35: {len(result.schemes)} found')

result = search_schemes('yojana', gender='female')
print(f'Schemes for women: {len(result.schemes)} found')
"
```

### Language Detection (Fully Offline)

```bash
cd sahayak/bhashini-lang
python -c "
import asyncio
from bhashini_lang.client import detect_language

async def test():
    # Hindi
    r = await detect_language('नमस्ते, मुझे गेहूं का भाव बताओ')
    print(f'Hindi: lang={r[\"language\"]}, confidence={r[\"confidence\"]:.2f}')

    # English
    r = await detect_language('What is the weather in Bhopal?')
    print(f'English: lang={r[\"language\"]}, confidence={r[\"confidence\"]:.2f}')

    # Hinglish (mixed)
    r = await detect_language('PM KISAN ka paisa kab aayega?')
    print(f'Hinglish: lang={r[\"language\"]}, confidence={r[\"confidence\"]:.2f}')

asyncio.run(test())
"
```

### TTL Cache

```bash
cd sahayak/govdata-india
python -c "
import time
from govdata_india.cache import TTLCache

cache = TTLCache(default_ttl=2.0)  # 2-second TTL for testing
cache.set('test', 'hello')
print(f'Immediate get: {cache.get(\"test\")}')  # hello

time.sleep(2.5)
print(f'After 2.5s: {cache.get(\"test\")}')  # None (expired)

# Custom TTL per key
cache.set('short', 'gone soon', ttl=0.5)
cache.set('long', 'stays', ttl=10.0)
time.sleep(1.0)
print(f'Short-lived: {cache.get(\"short\")}')  # None
print(f'Long-lived: {cache.get(\"long\")}')    # stays
"
```

---

## 4. Testing Against Live APIs

### Mandi Prices (Requires DATA_GOV_IN_API_KEY)

```bash
cd sahayak/govdata-india
python -c "
import asyncio, os
os.environ.setdefault('DATA_GOV_IN_API_KEY', 'YOUR_KEY_HERE')

from govdata_india.mandi import get_mandi_prices

async def test():
    result = await get_mandi_prices('wheat', state='Madhya Pradesh')
    print(f'Source: {result.source}')
    print(f'Prices found: {len(result.prices)}')
    for p in result.prices[:5]:
        print(f'  {p.mandi}: ₹{p.modal_price}/quintal ({p.variety}) - {p.date}')

asyncio.run(test())
"
```

### PM-KISAN Status (Requires DATA_GOV_IN_API_KEY)

```bash
cd sahayak/govdata-india
python -c "
import asyncio, os
os.environ.setdefault('DATA_GOV_IN_API_KEY', 'YOUR_KEY_HERE')

from govdata_india.pmkisan import get_pm_kisan_status

async def test():
    result = await get_pm_kisan_status('Madhya Pradesh', 'Bhopal')
    if result.status:
        print(f'State: {result.status.state}')
        print(f'District: {result.status.district}')
        print(f'Beneficiaries: {result.status.beneficiary_count}')
        print(f'Last installment: {result.status.last_installment}')
    else:
        print(f'Message: {result.message}')

asyncio.run(test())
"
```

### Weather (Requires DATA_GOV_IN_API_KEY)

```bash
cd sahayak/govdata-india
python -c "
import asyncio, os
os.environ.setdefault('DATA_GOV_IN_API_KEY', 'YOUR_KEY_HERE')

from govdata_india.weather import get_weather

async def test():
    result = await get_weather('Bhopal', 'Madhya Pradesh')
    if result.weather:
        w = result.weather
        print(f'{w.district}, {w.state}')
        print(f'Temp: {w.temp_min}°C - {w.temp_max}°C')
        print(f'Rainfall: {w.rainfall}mm, Humidity: {w.humidity}%')
        print(f'Forecast: {w.forecast}')
        print(f'Advisory: {w.advisory}')
    else:
        print(f'Message: {result.message}')

asyncio.run(test())
"
```

### Bhashini Translation (Requires BHASHINI_ULCA_USER_ID + API_KEY)

```bash
cd sahayak/bhashini-lang
python -c "
import asyncio, os
os.environ.setdefault('BHASHINI_ULCA_USER_ID', 'YOUR_ID')
os.environ.setdefault('BHASHINI_ULCA_API_KEY', 'YOUR_KEY')

from bhashini_lang.client import translate_text

async def test():
    result = await translate_text('Hello, how are you?', 'en', 'hi')
    print(f'en → hi: {result}')

    result = await translate_text('गेहूं का भाव कितना है', 'hi', 'en')
    print(f'hi → en: {result}')

asyncio.run(test())
"
```

---

## 5. Testing MCP Servers via stdio

MCP servers communicate over stdio (stdin/stdout JSON-RPC). You can test this directly:

### List Available Tools

```bash
cd sahayak/govdata-india
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m govdata_india.server
```

Expected: JSON response listing `mandi_prices`, `pm_kisan_status`, `weather_info`, `scheme_search` with their input schemas.

```bash
cd sahayak/bhashini-lang
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m bhashini_lang.server
```

Expected: JSON response listing `detect_language`, `translate`, `speech_to_text`, `text_to_speech`.

### Call a Tool via stdio

```bash
cd sahayak/govdata-india
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"scheme_search","arguments":{"query":"farmer pension","age":35}}}' | python -m govdata_india.server
```

This should return matching schemes without needing any API key (offline search).

### Using MCP Inspector

If you have the MCP Inspector CLI installed:

```bash
# Inspect govdata-india
npx @modelcontextprotocol/inspector python -m govdata_india.server --cwd sahayak/govdata-india

# Inspect bhashini-lang
npx @modelcontextprotocol/inspector python -m bhashini_lang.server --cwd sahayak/bhashini-lang
```

The Inspector provides a web UI to browse tools, call them interactively, and inspect responses.

---

## 6. Debugging Common Issues

### Issue: `ModuleNotFoundError: No module named 'govdata_india'`

**Cause**: Package not installed in editable mode.

```bash
cd sahayak/govdata-india
pip install -e ".[dev]"
```

Verify: `python -c "import govdata_india; print('OK')"`

### Issue: `FastMCP() got unexpected keyword argument(s): 'description'`

**Cause**: FastMCP v3 renamed `description` to `instructions`.

**Fix**: The server files already use `instructions=`. If you see this, make sure you're running the latest code:

```bash
pip install --upgrade fastmcp
```

### Issue: `httpx.ConnectTimeout` on data.gov.in calls

**Cause**: data.gov.in can be slow or temporarily down.

**Debug steps**:
1. Test the API directly:
   ```bash
   curl "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070?api-key=YOUR_KEY&format=json&limit=1&filters[commodity]=Wheat"
   ```
2. If the API is down, the TTL cache will serve stale data for cached queries
3. For uncached queries, the tool returns a structured error (not an exception)

### Issue: Bhashini returns empty transcription

**Debug steps**:
1. Check credentials:
   ```bash
   python -c "import os; print('User:', os.environ.get('BHASHINI_ULCA_USER_ID', 'NOT SET')); print('Key:', 'SET' if os.environ.get('BHASHINI_ULCA_API_KEY') else 'NOT SET')"
   ```
2. Test pipeline config fetch:
   ```bash
   cd sahayak/bhashini-lang
   python -c "
   import asyncio
   from bhashini_lang.client import _get_pipeline_config
   async def test():
       config = await _get_pipeline_config('asr', 'hi')
       print(f'Callback URL: {config[\"callback_url\"][:50]}...')
       print(f'Service ID: {config[\"service_id\"]}')
       print(f'Auth key: {\"SET\" if config[\"authorization_key\"] else \"EMPTY\"}')
   asyncio.run(test())
   "
   ```
3. If Bhashini fails, verify the Whisper fallback works:
   ```bash
   python -c "
   import asyncio
   from bhashini_lang.fallback import whisper_transcribe
   # This will fail without a real audio file, but tests the path
   result = asyncio.run(whisper_transcribe('dGVzdA==', 'hi'))
   print(result)
   "
   ```

### Issue: Scheme search returns 0 results

**Cause**: The query tokens don't match any text in `schemes.json`.

**Debug**:
```bash
cd sahayak/govdata-india
python -c "
from govdata_india.schemes import search_schemes

# Test with exact scheme name fragments
for q in ['KISAN', 'Awas', 'pension', 'insurance', 'farmer', 'loan', 'woman', 'Ujjwala']:
    r = search_schemes(q)
    print(f'  \"{q}\": {len(r.schemes)} results')
"
```

The search matches against `name + benefits + eligibility` fields. If your query term doesn't appear in these fields, it won't match. Check `sahayak/govdata-india/govdata_india/data/schemes.json` for the exact text.

### Issue: Tests fail with `asyncio` errors

**Cause**: pytest-asyncio strict mode requires explicit `@pytest.mark.asyncio` on async tests.

The repo's root `pyproject.toml` may set `asyncio_mode = "strict"`. All async tests in the codebase already have the decorator. If you add new async tests, always include:

```python
@pytest.mark.asyncio
async def test_my_new_test():
    ...
```

---

## 7. Debugging the Full Pipeline

### Step 1: Verify MCP Servers Start

```bash
# In separate terminals (or use & for background)

# Terminal 1: govdata-india
cd sahayak/govdata-india
python -m govdata_india.server
# Should hang waiting for stdio input — that's correct

# Terminal 2: bhashini-lang
cd sahayak/bhashini-lang
python -m bhashini_lang.server
# Same — hangs waiting for input
```

If either crashes on startup, you'll see the error immediately.

### Step 2: Verify OpenClaw Gateway Sees the MCP Servers

After starting the gateway with the Sahayak config:

```bash
# Check gateway logs for MCP server startup
# Look for lines like:
#   MCP server bhashini-lang started (pid: XXXX)
#   MCP server govdata-india started (pid: XXXX)
#   Agent sahayak loaded with 8 tools
```

If MCP servers fail to start, check:
- Python is in PATH: `which python`
- Working directory is correct (relative to repo root)
- Dependencies are installed: `pip list | grep fastmcp`

### Step 3: Test Text Flow Without WhatsApp

Use the OpenClaw CLI to send a test message directly:

```bash
# Send a test message to the Sahayak agent
openclaw message send --agent sahayak "गेहूं का भाव बताओ भोपाल में"
```

Watch the gateway logs for:
1. Agent receives message
2. Agent calls `detect_language` → `{language: "hi"}`
3. Agent calls `mandi_prices` → price data
4. Agent composes Hindi response

### Step 4: Test WhatsApp Integration

```bash
# Check WhatsApp connection status
openclaw channels status

# If not paired, pair WhatsApp
openclaw channels whatsapp pair
# Scan QR code from your phone

# Send a test message from your phone to the paired number
```

### Step 5: Inspect Agent Reasoning

To see what the agent is doing step-by-step, check the session logs:

```bash
# Find the latest session
ls -lt ~/.openclaw/agents/sahayak/sessions/ | head -5

# Read the session JSONL (each line is a turn)
# Look for tool_use entries to see which MCP tools were called
```

---

## 8. Writing New Tests

### Adding a Test for a New Scheme

```python
# In sahayak/govdata-india/tests/test_server.py

class TestSchemeSearch:
    def test_search_new_keyword(self):
        """Verify a new keyword matches expected schemes."""
        result = search_schemes("insurance")
        assert len(result.schemes) > 0
        # Check specific expected scheme
        names = [s.name for s in result.schemes]
        assert any("Bima" in n or "Suraksha" in n for n in names)
```

### Adding a Test with Mocked HTTP

```python
import pytest
import httpx
import respx

class TestNewFeature:
    @pytest.mark.asyncio
    @respx.mock
    async def test_api_call(self, mock_api_key):
        from govdata_india.mandi import get_mandi_prices, _cache
        _cache.clear()  # Always clear cache before mocked tests

        # Mock the specific API endpoint
        respx.get("https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070").mock(
            return_value=httpx.Response(200, json={
                "records": [
                    {"market": "TestMandi", "commodity": "Rice", "variety": "Basmati",
                     "min_price": "3000", "max_price": "3500", "modal_price": "3200",
                     "arrival_date": "21/03/2026"}
                ]
            })
        )

        result = await get_mandi_prices("rice")
        assert result.prices[0].commodity == "Rice"
```

**Key patterns for mocked tests**:
1. Always use `@respx.mock` decorator
2. Always clear `_cache` before the test (otherwise a previous test's cached result is returned)
3. Use the `mock_api_key` fixture from `conftest.py`
4. Mock the exact URL the code calls (including the resource ID path)

### Testing Error Paths

```python
@pytest.mark.asyncio
@respx.mock
async def test_timeout_handling(self, mock_api_key):
    from govdata_india.mandi import get_mandi_prices, _cache
    _cache.clear()

    # Simulate a timeout
    respx.get("https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070").mock(
        side_effect=httpx.ConnectTimeout("Connection timed out")
    )

    result = await get_mandi_prices("wheat")
    assert len(result.prices) == 0
    assert "error" in result.source  # Error captured in source field
```

---

## 9. Performance Profiling

### Measure Tool Response Times

```bash
cd sahayak/govdata-india
python -c "
import asyncio, time, os
os.environ.setdefault('DATA_GOV_IN_API_KEY', 'YOUR_KEY')

from govdata_india.mandi import get_mandi_prices, _cache

async def bench():
    _cache.clear()

    # Cold call (no cache)
    start = time.perf_counter()
    result = await get_mandi_prices('wheat', state='Madhya Pradesh')
    cold_ms = (time.perf_counter() - start) * 1000
    print(f'Cold call: {cold_ms:.0f}ms ({len(result.prices)} prices)')

    # Warm call (cached)
    start = time.perf_counter()
    result = await get_mandi_prices('wheat', state='Madhya Pradesh')
    warm_ms = (time.perf_counter() - start) * 1000
    print(f'Cached call: {warm_ms:.2f}ms ({len(result.prices)} prices)')

asyncio.run(bench())
"
```

Expected:
- Cold call: 500-3000ms (depends on data.gov.in latency)
- Cached call: <1ms

### Measure Scheme Search Performance

```bash
cd sahayak/govdata-india
python -c "
import time
from govdata_india.schemes import search_schemes

# First call loads JSON from disk
start = time.perf_counter()
search_schemes('farmer')
load_ms = (time.perf_counter() - start) * 1000
print(f'First call (with JSON load): {load_ms:.1f}ms')

# Subsequent calls use in-memory data
start = time.perf_counter()
for _ in range(1000):
    search_schemes('farmer pension', age=35, gender='female')
elapsed = (time.perf_counter() - start) * 1000
print(f'1000 filtered searches: {elapsed:.1f}ms ({elapsed/1000:.3f}ms each)')
"
```

---

## 10. Quick Reference

| What | Command |
|------|---------|
| Run all govdata tests | `cd sahayak/govdata-india && python -m pytest tests/ -v` |
| Run all bhashini tests | `cd sahayak/bhashini-lang && python -m pytest tests/ -v` |
| Run single test | `python -m pytest tests/test_server.py::TestSchemeSearch::test_search_by_keyword -v` |
| Run tests matching keyword | `python -m pytest tests/ -k "mandi" -v` |
| Run with print output | `python -m pytest tests/ -v -s` |
| Run with coverage | `python -m pytest tests/ --cov=govdata_india --cov-report=term-missing` |
| Check Python syntax | `python -c "import ast; ast.parse(open('file.py').read())"` |
| Test scheme search | `python -c "from govdata_india.schemes import search_schemes; print(search_schemes('farmer'))"` |
| Test language detection | `python -c "import asyncio; from bhashini_lang.client import detect_language; print(asyncio.run(detect_language('नमस्ते')))"` |
| List MCP tools (stdio) | `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \| python -m govdata_india.server` |
| MCP Inspector | `npx @modelcontextprotocol/inspector python -m govdata_india.server` |
| Check gateway logs | `tail -f /tmp/openclaw-gateway.log` (Linux/Mac) |
| WhatsApp status | `openclaw channels status` |
