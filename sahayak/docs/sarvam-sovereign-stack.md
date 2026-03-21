# Sarvam AI — Sovereign Indian Stack

## Why Sarvam?

Sahayak can run on a **100% sovereign Indian AI stack** — no dependency on US cloud APIs (OpenAI, Anthropic). This matters for:

- **IndiaAI Mission alignment**: Government pitch requires demonstrating data sovereignty
- **DPDP Act compliance**: User data (voice, text) never leaves Indian infrastructure
- **Cost**: Sarvam LLMs (30B, 105B) are **free** — ₹0 per token
- **Latency**: Indian data centers = lower latency for Indian users
- **Language quality**: Models trained on Indian language data outperform general-purpose models on Hindi/regional languages

## What Sarvam Provides

| Service | Sarvam Product | Replaces | Pricing |
|---------|---------------|----------|---------|
| **LLM (Agent brain)** | Sarvam-M (30B/105B) | Claude Sonnet | Free (₹0/token) |
| **Speech-to-Text** | Saaras v3 | OpenAI Whisper | ₹30/hour |
| **Text-to-Speech** | Bulbul v3 (30+ voices) | Edge TTS | ₹30/10K chars |
| **Translation** | Mayura / Sarvam Translate | Bhashini NMT | ₹20/10K chars |
| **Language Detection** | text-lid | Devanagari heuristic | ₹3.50/10K chars |
| **Transliteration** | Transliterate API | — | ₹20/10K chars |

**Free tier**: ₹1,000 credits on signup (enough for ~30 hours of STT or ~300K characters of TTS).

## Configuration Profiles

Sahayak ships three config profiles:

| Config File | LLM | Language Services | Cost |
|-------------|-----|-------------------|------|
| `openclaw.sahayak.json` | Claude Sonnet (primary) + Ollama (fallback) | Auto (Sarvam if key set, else Bhashini) | API costs |
| `openclaw.sahayak.dev.json` | Sarvam-M (primary) + Ollama (fallback) | Auto | Free |
| `openclaw.sahayak.sovereign.json` | Sarvam-M only | Sarvam only | Free (within ₹1K credits) |

### Using the Sovereign Config

```bash
# Set your Sarvam API key
export SARVAM_API_KEY=your_key_here
export DATA_GOV_IN_API_KEY=your_data_gov_key

# Copy sovereign config
cp sahayak/openclaw.sahayak.sovereign.json ~/.openclaw/openclaw.json

# Start the gateway
openclaw gateway run
```

In this mode, the entire stack is:
- **LLM**: Sarvam-M (Indian servers)
- **ASR**: Sarvam Saaras v3 (Indian servers)
- **TTS**: Sarvam Bulbul v3 (Indian servers)
- **Translation**: Sarvam Mayura (Indian servers)
- **Language Detection**: Sarvam text-lid (Indian servers)
- **Government Data**: data.gov.in (Indian government servers)

Zero bytes leave India.

## Getting a Sarvam API Key

1. Go to [sarvam.ai](https://www.sarvam.ai) → Sign up
2. Access the dashboard → Get your API subscription key
3. You receive **₹1,000 free credits** immediately
4. Set it: `export SARVAM_API_KEY=your_key`

## Language Provider Switching

The `bhashini-lang` MCP server supports three providers via the `LANG_PROVIDER` env var:

| Value | Behavior |
|-------|----------|
| `auto` (default) | Uses Sarvam if `SARVAM_API_KEY` is set, otherwise Bhashini |
| `sarvam` | Forces Sarvam AI for all language services |
| `bhashini` | Forces Bhashini ULCA for all language services |

The fallback chain works across providers:

```
Primary provider (Sarvam or Bhashini)
  ↓ failure?
Other provider (Bhashini or Sarvam)
  ↓ failure?
Final fallback:
  ASR → OpenAI Whisper
  NMT → pass-through (LLM handles it)
  TTS → empty (Edge TTS handles output)
```

## Sarvam API Reference

Base URL: `https://api.sarvam.ai`
Auth header: `api-subscription-key: YOUR_KEY`

### Language Detection
```
POST /text-lid
Body: {"input": "नमस्ते दुनिया"}
Response: {"language_code": "hi-IN", "script_code": "Deva"}
```

### Translation
```
POST /translate
Body: {
  "input": "Hello world",
  "source_language_code": "en-IN",
  "target_language_code": "hi-IN",
  "model": "mayura:v1",
  "mode": "colloquial"
}
Response: {"translated_text": "नमस्ते दुनिया"}
```

### Speech-to-Text
```
POST /speech-to-text
Content-Type: multipart/form-data
Fields: model=saaras:v3, language_code=hi-IN
File: audio file (WAV/OGG/MP3)
Response: {"transcript": "गेहूं का भाव बताओ", "language_code": "hi-IN"}
```

### Text-to-Speech
```
POST /text-to-speech
Body: {
  "text": "गेहूं का भाव दो हज़ार एक सौ पचास रुपये है",
  "target_language_code": "hi-IN",
  "speaker": "meera",
  "model": "bulbul:v3"
}
Response: {"audios": ["<base64-wav>"]}
```

### Chat Completion (LLM)
```
POST /v1/chat/completions
Authorization: Bearer YOUR_KEY
Body: {
  "model": "sarvam-m",
  "messages": [{"role": "user", "content": "..."}]
}
```

OpenAI-compatible format — works directly with OpenClaw's provider system.

## Supported Languages

Sarvam supports all 22 scheduled Indian languages + English:

| Code | Language | ASR | TTS | Translation |
|------|----------|-----|-----|-------------|
| hi-IN | Hindi | Yes | Yes | Yes |
| en-IN | English | Yes | Yes | Yes |
| bn-IN | Bengali | Yes | Yes | Yes |
| ta-IN | Tamil | Yes | Yes | Yes |
| te-IN | Telugu | Yes | Yes | Yes |
| mr-IN | Marathi | Yes | Yes | Yes |
| gu-IN | Gujarati | Yes | Yes | Yes |
| kn-IN | Kannada | Yes | Yes | Yes |
| ml-IN | Malayalam | Yes | Yes | Yes |
| pa-IN | Punjabi | Yes | Yes | Yes |
| od-IN | Odia | Yes | Yes | Yes |

TTS (Bulbul v3) supports 11 languages with 30+ speaker voices.

## Cost Comparison

For a typical demo day (50 voice interactions, ~2 min each):

| Component | Anthropic + OpenAI Stack | Sarvam Sovereign Stack |
|-----------|------------------------|----------------------|
| LLM (agent) | ~$5 (Sonnet) | ₹0 (free) |
| ASR (voice → text) | ~$1 (Whisper) | ~₹50 (Sarvam) |
| TTS (text → voice) | $0 (Edge TTS) | ~₹15 (Bulbul) |
| Translation | $0 (Bhashini free) | ~₹10 (Mayura) |
| **Total** | **~$6 (~₹500)** | **~₹75 (~$0.90)** |

The sovereign stack is **~6x cheaper** and keeps all data in India.

## Testing Sarvam Integration

```bash
# Test language detection
cd sahayak/bhashini-lang
SARVAM_API_KEY=your_key LANG_PROVIDER=sarvam python -c "
import asyncio
from bhashini_lang.sarvam import detect_language
result = asyncio.run(detect_language('नमस्ते, मुझे गेहूं का भाव बताओ'))
print(result)
"

# Test translation
SARVAM_API_KEY=your_key LANG_PROVIDER=sarvam python -c "
import asyncio
from bhashini_lang.sarvam import translate_text
result = asyncio.run(translate_text('Hello, what is the wheat price?', 'en', 'hi'))
print(result)
"

# Test TTS
SARVAM_API_KEY=your_key LANG_PROVIDER=sarvam python -c "
import asyncio
from bhashini_lang.sarvam import text_to_speech
result = asyncio.run(text_to_speech('नमस्ते', 'hi'))
print(f'Audio length: {len(result[\"audio_base64\"])} chars')
"
```

## Sovereign Stack for IndiaAI Pitch

When presenting to IndiaAI Mission, the sovereign config lets you demonstrate:

1. **No foreign API dependency** — LLM, ASR, TTS, NMT all run on Indian infra
2. **Data sovereignty** — Voice data never leaves India (DPDP Act ready)
3. **Cost efficiency** — Free LLM, minimal language service costs
4. **Indian language first** — Models trained specifically for Indian languages
5. **Government data integration** — Direct data.gov.in API access
6. **Scalable** — Sarvam offers private cloud and on-premises deployment
