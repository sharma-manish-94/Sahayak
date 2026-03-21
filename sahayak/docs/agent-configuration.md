# Agent Configuration

## Overview

Sahayak uses a single agent powered by Claude Sonnet that handles all user interactions. The agent uses LLM-driven tool selection rather than a keyword-based router — Claude naturally understands Hindi, English, Hinglish, and compound queries without any custom routing code.

## Agent Identity

| Property | Value |
|----------|-------|
| **ID** | `sahayak` |
| **Name** | Sahayak |
| **Model** | `anthropic/claude-sonnet-4-20250514` |
| **System Prompt** | `sahayak/agent/SYSTEM.md` |
| **Default** | Yes (handles all incoming messages) |

## System Prompt Design

The system prompt (`sahayak/agent/SYSTEM.md`) defines:

### Language Rules
- Detect user's language and respond in the same language
- Hindi voice inputs assumed (most WhatsApp voice notes are in Hindi)
- Hinglish (mixed Hindi-English) supported naturally

### Tool Selection Guidelines
The prompt maps user intents to specific tools:

| User Intent | Tool(s) Called |
|-------------|---------------|
| Crop/mandi prices | `mandi_prices` |
| PM-KISAN status | `pm_kisan_status` |
| Weather/farming advice | `weather_info` |
| Government schemes | `scheme_search` |
| Language detection | `detect_language` |
| Translation needed | `translate` |

### Response Style
- Under 150 words (optimized for voice)
- Simple language, no bureaucratic jargon
- Always cite data source ("data.gov.in ke anusaar")
- Clear formatting for prices ("₹2,150/quintal")
- Honest about unavailable data — never fabricate

## Channel Binding

```yaml
bindings:
  - agentId: sahayak
    match:
      channel: whatsapp
```

The Sahayak agent is bound exclusively to the WhatsApp channel. All WhatsApp messages are routed to this agent.

## MCP Tool Availability

The agent has access to 8 tools across 2 MCP servers:

### From `bhashini-lang`:
1. `detect_language(text)` → language code + confidence
2. `translate(text, source_lang, target_lang)` → translated text
3. `speech_to_text(audio_base64, source_lang?)` → transcribed text
4. `text_to_speech(text, target_lang?, gender?)` → audio base64

### From `govdata-india`:
5. `mandi_prices(commodity, state?, district?)` → price list
6. `pm_kisan_status(state, district, block?)` → beneficiary data
7. `weather_info(district, state)` → weather + advisory
8. `scheme_search(query, age?, gender?, category?)` → matching schemes

## Voice Pipeline Integration

### Inbound Voice (Speech → Agent)
1. WhatsApp voice note received
2. OpenClaw's Whisper integration transcribes audio → text
3. Transcript delivered to agent as text message
4. Agent processes as normal text (Hindi detection built-in)

Configuration:
```yaml
tools:
  media:
    audio:
      provider: openai
      model: whisper-1
```

### Outbound Voice (Agent → Speech)
1. Agent composes text response
2. Edge TTS synthesizes Hindi audio with `hi-IN-SwaraNeural` voice
3. Audio sent back as WhatsApp voice note

Configuration:
```yaml
tts:
  auto: inbound    # Auto-TTS for responses to voice messages
  provider: edge
  edge:
    voice: hi-IN-SwaraNeural
    lang: hi-IN
```

The `auto: inbound` setting means TTS is automatically applied when the user sent a voice note, creating a natural voice-in/voice-out experience.

## Example Interaction Flows

### Simple Hindi Query
```
User (voice): "गेहूं का भाव बताओ भोपाल में"
Agent:
  1. detect_language("गेहूं का भाव बताओ भोपाल में") → {language: "hi"}
  2. mandi_prices(commodity="wheat", district="Bhopal", state="Madhya Pradesh")
  3. Compose Hindi response with price data
Response (voice): "data.gov.in ke anusaar, Bhopal mandi mein gehun ₹2,150/quintal..."
```

### Compound Hinglish Query
```
User (text): "Bhopal mein gehun ka rate aur mausam batao"
Agent:
  1. Detect Hinglish — respond in Hinglish
  2. mandi_prices(commodity="wheat", district="Bhopal", state="Madhya Pradesh")
  3. weather_info(district="Bhopal", state="Madhya Pradesh")
  4. Combine both results in single response
Response (text): "Gehun: ₹2,150/quintal (Bhopal mandi).\nMausam: 38°C, saaf aasmaan..."
```

### Scheme Discovery
```
User (text): "What government schemes are available for women farmers over 50?"
Agent:
  1. Detect English
  2. scheme_search(query="farmer", gender="female", age=50)
  3. List matching schemes with eligibility and how-to-apply
Response (text): "Here are relevant schemes:\n1. PM-KISAN: ₹6,000/year..."
```
