# Deployment Guide

## Prerequisites

- Node.js 22+ (for OpenClaw gateway)
- Python 3.11+ (for MCP servers)
- Docker & Docker Compose (for containerized deployment)
- WhatsApp Business API access or WhatsApp Web pairing

## Environment Variables

Create a `.env` file in the repo root:

```bash
# data.gov.in (free registration at data.gov.in)
DATA_GOV_IN_API_KEY=your_api_key_here

# Bhashini ULCA (free PoC tier at bhashini.gov.in/ulca)
BHASHINI_ULCA_USER_ID=your_user_id
BHASHINI_ULCA_API_KEY=your_api_key

# OpenAI (for Whisper ASR fallback)
OPENAI_API_KEY=your_openai_key

# Anthropic (for Claude Sonnet agent)
ANTHROPIC_API_KEY=your_anthropic_key
```

## Option 1: Local Development

### Step 1: Install OpenClaw

```bash
pnpm install
pnpm build
```

### Step 2: Install MCP Server Dependencies

```bash
# govdata-india
cd sahayak/govdata-india
pip install -e ".[dev]"

# bhashini-lang
cd ../bhashini-lang
pip install -e ".[dev]"
```

### Step 3: Run Tests

```bash
# Test govdata-india
cd sahayak/govdata-india
python -m pytest tests/ -v

# Test bhashini-lang
cd ../bhashini-lang
python -m pytest tests/ -v
```

### Step 4: Start Gateway

```bash
# From repo root
openclaw gateway run --bind loopback --port 18789
```

### Step 5: Pair WhatsApp

```bash
openclaw channels whatsapp pair
# Scan the QR code with WhatsApp on your phone
```

### Step 6: Test

Send a message to the paired WhatsApp number:
- Text: "PM KISAN status batao"
- Voice: Record a Hindi voice note asking about mandi prices

## Option 2: Docker Deployment

### Step 1: Build and Start

```bash
cd sahayak
docker compose -f docker-compose.sahayak.yml up --build
```

### Step 2: Verify

```bash
# Check all containers are running
docker compose -f docker-compose.sahayak.yml ps

# Check gateway logs
docker compose -f docker-compose.sahayak.yml logs openclaw

# Check MCP server logs
docker compose -f docker-compose.sahayak.yml logs govdata-india
docker compose -f docker-compose.sahayak.yml logs bhashini-lang
```

## Verifying the Setup

### 1. MCP Server Health

```bash
# Test govdata-india server directly
cd sahayak/govdata-india
python -c "from govdata_india.schemes import search_schemes; print(search_schemes('farmer'))"

# Test bhashini-lang language detection
cd sahayak/bhashini-lang
python -c "import asyncio; from bhashini_lang.client import detect_language; print(asyncio.run(detect_language('नमस्ते')))"
```

### 2. Gateway Logs

After starting the gateway, check for:
```
MCP server bhashini-lang started (pid: XXXX)
MCP server govdata-india started (pid: XXXX)
Agent sahayak loaded with 8 tools
WhatsApp channel connected
```

### 3. End-to-End Test

Send these test messages on WhatsApp:

| Message | Expected Response |
|---------|------------------|
| "गेहूं का भाव बताओ" | Hindi response with wheat mandi prices |
| "PM KISAN ka paisa?" | Hinglish response about PM-KISAN status |
| "What schemes for farmers?" | English list of farmer schemes |
| Hindi voice note | Hindi voice note reply |

## Performance Targets

| Metric | Target |
|--------|--------|
| Text response latency | < 8 seconds |
| Voice-to-voice latency | < 15 seconds |
| Scheme search (offline) | < 100ms |
| Cached API response | < 200ms |

## Troubleshooting

### MCP server won't start
- Check Python version: `python --version` (needs 3.11+)
- Check dependencies: `pip install -e ".[dev]"` in each MCP directory
- Check env vars are set

### No response from agent
- Check gateway logs for errors
- Verify Anthropic API key is set and valid
- Check WhatsApp is paired: `openclaw channels status`

### API returning empty data
- Verify `DATA_GOV_IN_API_KEY` is valid
- Check data.gov.in API status
- Try a different commodity/state — some combinations have no data

### Voice notes not working
- Verify `OPENAI_API_KEY` is set (for Whisper)
- Check TTS config in openclaw.yaml
- Test with text first to isolate voice pipeline issues
