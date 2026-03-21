# Sahayak Architecture

## Overview

Sahayak is a WhatsApp-first AI assistant that helps Indian citizens access government services in their own language. Built on top of the OpenClaw monorepo, it extends the platform with two Python MCP (Model Context Protocol) servers, a dedicated agent configuration, and security hardening.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WhatsApp (User)                          │
│              Voice Note / Text Message                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenClaw Gateway (localhost:18789)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  WhatsApp     │  │   Whisper    │  │   Edge TTS       │  │
│  │  Extension    │  │   ASR        │  │   hi-IN-Swara    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘  │
│         │                 │                  │              │
│         ▼                 ▼                  ▼              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Sahayak Agent (Claude Sonnet)           │   │
│  │  - Detects language from user message                │   │
│  │  - Selects appropriate MCP tools                     │   │
│  │  - Composes response in user's language              │   │
│  └──────────────┬───────────────────┬──────────────────┘   │
│                 │                   │                       │
└─────────────────┼───────────────────┼───────────────────────┘
                  │                   │
      ┌───────────┘                   └───────────┐
      ▼                                           ▼
┌─────────────────────┐              ┌──────────────────────┐
│  bhashini-lang MCP  │              │  govdata-india MCP   │
│  (Python/FastMCP)   │              │  (Python/FastMCP)    │
│                     │              │                      │
│  Tools:             │              │  Tools:              │
│  • detect_language  │              │  • mandi_prices      │
│  • translate        │              │  • pm_kisan_status   │
│  • speech_to_text   │              │  • weather_info      │
│  • text_to_speech   │              │  • scheme_search     │
└─────────┬───────────┘              └──────────┬───────────┘
          │                                     │
          ▼                                     ▼
┌─────────────────────┐              ┌──────────────────────┐
│  Bhashini ULCA API  │              │  data.gov.in API     │
│  (meity-auth)       │              │  (Agmarknet, IMD,    │
│  Fallback: Whisper  │              │   PM-KISAN)          │
└─────────────────────┘              │  + schemes.json      │
                                     └──────────────────────┘
```

## Key Design Decisions

### 1. Single Agent with LLM-Driven Tool Selection

Instead of building a keyword-based router (regex on Hindi text), Sahayak uses a single Claude Sonnet agent that naturally handles:

- **Multilingual intent detection**: Understanding "गेहूं का भाव" (wheat price), "gehun ka bhaav" (Hinglish), and "wheat price" all mean the same thing
- **Compound queries**: "mandi price AND weather batao" triggers multiple tools in one turn
- **Typo tolerance**: LLM handles misspellings far better than regex
- **Zero routing code**: No custom intent classifier to maintain

### 2. MCP Over Direct API Calls

Government APIs are wrapped in MCP servers rather than called directly by the agent because:

- **Tool schema**: MCP provides typed tool definitions the LLM can reason about
- **Isolation**: Each data source runs in its own process with its own credentials
- **Caching**: TTL caches live in the MCP server, transparent to the agent
- **Testability**: Mock HTTP responses at the MCP level without touching agent logic
- **Extensibility**: Add new data sources (DigiLocker, API Setu) as new MCP servers

### 3. Bhashini with Fallback Chain

The language pipeline has a cascading fallback strategy:

| Service | Primary Provider | Fallback |
|---------|-----------------|----------|
| ASR (Speech → Text) | Bhashini ULCA | OpenAI Whisper |
| NMT (Translation) | Bhashini ULCA | Pass-through (LLM handles it) |
| TTS (Text → Speech) | Bhashini ULCA | Edge TTS (hi-IN-SwaraNeural) |
| LID (Language Detection) | Devanagari heuristic | — |

This ensures the demo works even if Bhashini is temporarily down.

### 4. Localhost-Only Gateway

The OpenClaw gateway binds to `localhost` only — no public exposure. WhatsApp messages arrive via the WhatsApp extension's existing webhook infrastructure, which handles its own authentication.

## Data Flow

### Inbound Voice Message

```
1. User sends Hindi voice note on WhatsApp
2. WhatsApp extension receives audio via webhook
3. OpenClaw routes audio to Whisper ASR → Hindi text transcript
4. Transcript sent to Sahayak agent as user message
5. Agent calls detect_language("गेहूं का भाव बताओ भोपाल में")
   → {language: "hi", confidence: 0.95}
6. Agent identifies intent: mandi price query
7. Agent calls mandi_prices(commodity="wheat", district="Bhopal", state="Madhya Pradesh")
   → {prices: [{mandi: "Bhopal", modal_price: 2150, ...}]}
8. Agent composes Hindi response:
   "data.gov.in ke anusaar, Bhopal mandi mein gehun ka bhav ₹2,150/quintal hai (21 March 2026)"
9. Edge TTS converts response to hi-IN audio
10. Audio sent back to user as WhatsApp voice note
```

### Inbound Text Message

```
1. User sends text "PM KISAN ka paisa kab aayega?" on WhatsApp
2. WhatsApp extension delivers text to Sahayak agent
3. Agent detects Hinglish, identifies PM-KISAN intent
4. Agent calls pm_kisan_status(state="...", district="...")
   and scheme_search(query="PM KISAN")
5. Agent composes response in Hinglish
6. Text response sent back on WhatsApp
```

## Process Model

```
OpenClaw Gateway (Node.js)
  ├── WhatsApp Extension (webhook listener)
  ├── Agent Runtime (Sahayak agent with Claude Sonnet)
  ├── MCP: bhashini-lang (Python subprocess, stdio)
  ├── MCP: govdata-india (Python subprocess, stdio)
  ├── Whisper ASR (OpenAI API call)
  └── Edge TTS (local synthesis)
```

Each MCP server runs as a child process of the gateway, communicating over stdio (standard MCP transport). The gateway spawns them on startup and manages their lifecycle.
