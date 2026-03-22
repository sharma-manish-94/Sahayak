# Sahayak (सहायक)

**WhatsApp AI assistant for Indian government services — in Hindi, English, and Hinglish.**

Sahayak helps Indian citizens discover government schemes, check agricultural mandi prices, get weather advisories, and track PM-KISAN benefit status — all through WhatsApp voice notes or text messages in their own language.

Built on [OpenClaw](https://github.com/nicepkg/openclaw) and powered by [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

---

## How It Works

```
WhatsApp (Voice/Text)
        │
        ▼
OpenClaw Gateway (localhost:18789)
  ├── WhatsApp Extension
  ├── Whisper ASR / Edge TTS
  └── Sahayak Agent (Claude Sonnet)
        ├── bhashini-lang MCP ──→ Bhashini ULCA / Sarvam AI
        └── govdata-india MCP ──→ data.gov.in APIs
```

A farmer sends a Hindi voice note asking "गेहूं का भाव बताओ भोपाल में" (tell me wheat price in Bhopal). Sahayak transcribes the audio, understands the intent, fetches live mandi prices from data.gov.in, and replies with a voice note in Hindi — all in under 15 seconds.

## Features

- **Multilingual**: Hindi, English, Hinglish — detects language automatically
- **Voice-first**: Send a voice note, get a voice reply
- **Mandi Prices**: Live agricultural commodity prices from 2,000+ mandis via data.gov.in
- **PM-KISAN Status**: Beneficiary count and installment data by district
- **Weather Advisory**: District-level weather with farming recommendations
- **Scheme Discovery**: Search 15+ central government schemes filtered by age, gender, category
- **Profile-aware**: Conversationally collects state, district, age, category for personalized results
- **Sovereign option**: Run 100% on Indian AI stack (Sarvam AI) with no US cloud dependencies

## Quick Start

### Prerequisites

- **Node.js 22+** and **Python 3.11+**
- **Git**, **Docker & Docker Compose** (for containerized deployment)
- API keys (all free tier):
  - [data.gov.in](https://data.gov.in/) — `DATA_GOV_IN_API_KEY`
  - [Bhashini ULCA](https://bhashini.gov.in/ulca) — `BHASHINI_ULCA_USER_ID` + `BHASHINI_ULCA_API_KEY`
  - [Anthropic](https://console.anthropic.com/) — `ANTHROPIC_API_KEY` (or use local LLM)

### 1. Clone and Install

```bash
git clone https://github.com/anthropics/sahayak.git
cd sahayak

# Install MCP servers
cd sahayak/govdata-india && pip install -e ".[dev]"
cd ../bhashini-lang && pip install -e ".[dev]"

# Install OpenClaw gateway (from repo root)
cd ../.. && npm install
```

### 2. Set Environment Variables

```bash
export DATA_GOV_IN_API_KEY="your-key"
export BHASHINI_ULCA_USER_ID="your-user-id"
export BHASHINI_ULCA_API_KEY="your-api-key"
export ANTHROPIC_API_KEY="your-key"
```

### 3. Run Tests

```bash
cd sahayak/govdata-india && python -m pytest tests/ -v
cd ../bhashini-lang && python -m pytest tests/ -v
```

### 4. Start the Gateway

```bash
# From repo root
npx openclaw --config sahayak/openclaw.sahayak.json
```

### 5. Pair WhatsApp

Scan the QR code shown in the terminal with WhatsApp (Linked Devices). Send a message — Sahayak will reply.

### Docker Deployment

```bash
cd sahayak
docker compose -f docker-compose.sahayak.yml up --build
```

## Project Structure

```
sahayak/
├── agent/
│   └── SYSTEM.md                 # Agent persona and behavior rules
├── bhashini-lang/                # MCP server: language services
│   ├── bhashini_lang/
│   │   ├── server.py             # FastMCP tools: detect, translate, ASR, TTS
│   │   ├── client.py             # Bhashini ULCA API client
│   │   ├── sarvam.py             # Sarvam AI client (sovereign alternative)
│   │   ├── fallback.py           # Whisper / pass-through fallbacks
│   │   └── types.py              # Pydantic response models
│   └── tests/
├── govdata-india/                # MCP server: government data APIs
│   ├── govdata_india/
│   │   ├── server.py             # FastMCP tools: mandi, PM-KISAN, weather, schemes
│   │   ├── mandi.py              # Agricultural market price API
│   │   ├── pmkisan.py            # PM-KISAN beneficiary status API
│   │   ├── weather.py            # IMD weather + farming advisory
│   │   ├── schemes.py            # Offline scheme search engine
│   │   ├── cache.py              # TTL cache + HTTP retry helpers
│   │   ├── types.py              # Pydantic response models
│   │   └── data/schemes.json     # Curated scheme database
│   └── tests/
├── docs/                         # Architecture, security, deployment docs
├── openclaw.sahayak.json         # Production config (Claude Sonnet)
├── openclaw.sahayak.dev.json     # Dev config (local Ollama models)
├── openclaw.sahayak.sovereign.json  # Sovereign config (100% Indian stack)
└── docker-compose.sahayak.yml    # Container orchestration
```

## MCP Tools

### bhashini-lang (Language Services)

| Tool | Description |
|------|-------------|
| `detect_language` | Detect language from text (Hindi, English, Tamil, Telugu, etc.) |
| `translate` | Translate between 13 Indian languages and English |
| `speech_to_text` | Transcribe voice audio to text (ASR) |
| `text_to_speech` | Convert text to speech audio (TTS) |

### govdata-india (Government Data)

| Tool | Description |
|------|-------------|
| `mandi_prices` | Agricultural commodity prices from data.gov.in (6h cache) |
| `pm_kisan_status` | PM-KISAN beneficiary data by state/district (12h cache) |
| `weather_info` | District weather + farming advisory from IMD (3h cache) |
| `scheme_search` | Search 15+ central schemes by profile (age, gender, category) |

## Configuration Modes

| Config File | LLM | Language Provider | Use Case |
|-------------|-----|-------------------|----------|
| `openclaw.sahayak.json` | Claude Sonnet | Bhashini ULCA | Production |
| `openclaw.sahayak.dev.json` | Ollama (Qwen 2.5 14B) | Bhashini ULCA | Local development |
| `openclaw.sahayak.sovereign.json` | Sarvam AI | Sarvam AI | 100% Indian stack |

## Security

Sahayak follows defense-in-depth principles:

- Gateway bound to `localhost` only — not network-accessible
- Tool deny list blocks `bash`, `computer`, `file_write`, `file_edit`
- Only WhatsApp plugin loaded — all others disabled
- Group messages disabled — DM only
- All secrets via environment variables — never hardcoded
- Docker containers: read-only FS, no privilege escalation, all capabilities dropped
- ClawHub marketplace disabled — only Sahayak skills allowed

See [docs/security.md](docs/security.md) for the full threat model.

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design, data flows, design decisions |
| [Security](docs/security.md) | Hardening measures and threat model |
| [Deployment](docs/deployment.md) | Local dev and Docker setup |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | In-depth onboarding for new contributors |
| [Bhashini Lang MCP](docs/mcp-bhashini-lang.md) | Language server reference |
| [GovData India MCP](docs/mcp-govdata-india.md) | Data server reference |
| [Local LLM Setup](docs/local-llm-setup.md) | Ollama configuration guide |
| [Sarvam Sovereign Stack](docs/sarvam-sovereign-stack.md) | 100% Indian AI setup |

## Tech Stack

- **Runtime**: Python 3.11+ (MCP servers), Node.js 22+ (OpenClaw gateway)
- **MCP Framework**: [FastMCP](https://github.com/jlowin/fastmcp) 2.0+
- **HTTP Client**: httpx (async)
- **Validation**: Pydantic 2.0+
- **LLM**: Claude Sonnet (production) / Ollama (dev) / Sarvam AI (sovereign)
- **Language APIs**: Bhashini ULCA, Sarvam AI
- **Data APIs**: data.gov.in (Agmarknet, PM-KISAN, IMD)
- **Testing**: pytest, pytest-asyncio, respx
- **Deployment**: Docker Compose

## Contributing

See the [Developer Guide](docs/DEVELOPER_GUIDE.md) for setup instructions, architecture walkthrough, and contribution guidelines.

## License

MIT
