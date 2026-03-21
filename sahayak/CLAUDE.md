# Sahayak Development Guide

Sahayak-specific code lives in this directory. It extends the OpenClaw monorepo with two Python MCP servers and agent configuration.

## Structure

- `agent/SYSTEM.md` — Agent system prompt (Sahayak persona)
- `bhashini-lang/` — MCP server for Bhashini ULCA language services (ASR, NMT, TTS, LID)
- `govdata-india/` — MCP server for Indian government data APIs (mandi, PM-KISAN, weather, schemes)
- `docker-compose.sahayak.yml` — Container setup for demo

## MCP Servers

Both servers use FastMCP and follow the same pattern:
- `server.py` — FastMCP entry point with `@mcp.tool()` decorated functions
- Run via `python -m <package>.server` (stdio transport for OpenClaw)

### govdata-india
```bash
cd sahayak/govdata-india
pip install -e ".[dev]"
python -m pytest tests/
```
Requires: `DATA_GOV_IN_API_KEY` env var (free from data.gov.in)

### bhashini-lang
```bash
cd sahayak/bhashini-lang
pip install -e ".[dev]"
python -m pytest tests/
```
Requires: `BHASHINI_ULCA_USER_ID` + `BHASHINI_ULCA_API_KEY` env vars (free PoC tier from bhashini.gov.in/ulca)

## Testing

Tests use `respx` to mock HTTP calls. Run from each MCP server directory:
```bash
python -m pytest tests/ -v
```

## Key Design Decisions

- Single agent with LLM-driven tool selection (no keyword router)
- Structured error responses (not exceptions) — the LLM reasons about failures
- All API keys via environment variables — no plaintext in config
- Bhashini fallback chain: Bhashini → Whisper (ASR) / pass-through (NMT) / Edge TTS (TTS)
