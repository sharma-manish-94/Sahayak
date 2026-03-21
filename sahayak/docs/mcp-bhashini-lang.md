# bhashini-lang MCP Server

## Overview

The `bhashini-lang` MCP server provides multilingual language services for Indian languages via the [Bhashini ULCA](https://bhashini.gov.in/ulca) platform. It enables the Sahayak agent to detect languages, translate between Indian languages and English, transcribe speech, and synthesize speech — essential for serving India's diverse linguistic landscape.

## Tools

### `detect_language`

Detects the language of input text. Uses a fast Devanagari character heuristic (no API call).

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Text to detect language for |

**Output:**
```json
{
  "language": "hi",
  "confidence": 0.95
}
```

**Detection Logic:**
```
1. Count Devanagari characters (U+0900–U+097F) in text
2. Count total alphabetic characters
3. Compute ratio = devanagari / total_alpha
4. If ratio > 0.5 → Hindi (confidence = min(0.95, ratio))
5. If ratio > 0.1 → Hindi (confidence = ratio)
6. Else → English (confidence = min(0.95, 1 - ratio))
```

This heuristic is fast, offline, and accurate for the Hindi/English binary that covers 95%+ of Sahayak's traffic. For other Indian languages, the Bhashini ULCA pipeline can be extended.

---

### `translate`

Translates text between Indian languages and English using Bhashini's Neural Machine Translation (NMT) models.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Text to translate |
| `source_lang` | string | Yes | ISO 639-1 source language code |
| `target_lang` | string | Yes | ISO 639-1 target language code |

**Supported Languages:**
`hi` (Hindi), `en` (English), `bn` (Bengali), `ta` (Tamil), `te` (Telugu), `mr` (Marathi), `gu` (Gujarati), `kn` (Kannada), `ml` (Malayalam), `pa` (Punjabi), `or` (Odia), `as` (Assamese), `ur` (Urdu)

**Output:**
```json
{
  "translated_text": "नमस्ते दुनिया",
  "source_lang": "en",
  "target_lang": "hi"
}
```

**Fallback:** If Bhashini NMT is unavailable, returns the original text (pass-through). The LLM agent can still process the message since Claude understands Hindi natively.

---

### `speech_to_text`

Transcribes speech audio to text using Bhashini ASR (Automatic Speech Recognition).

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `audio_base64` | string | Yes | Base64-encoded audio data (OGG/WAV format) |
| `source_lang` | string | No | Expected language code. Defaults to "hi" (Hindi) |

**Output:**
```json
{
  "text": "गेहूं का भाव बताओ",
  "detected_lang": "hi"
}
```

**Fallback:** If Bhashini ASR fails, falls back to OpenAI Whisper API:
1. Decode base64 audio to temp file
2. POST to `api.openai.com/v1/audio/transcriptions`
3. Return Whisper transcription

Note: In practice, OpenClaw's built-in Whisper integration handles most ASR. This tool is available for cases where Bhashini's Indian-language-specific models provide better accuracy.

---

### `text_to_speech`

Converts text to speech audio using Bhashini TTS.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Text to synthesize |
| `target_lang` | string | No | Language code. Defaults to "hi" |
| `gender` | string | No | Voice gender — "male" or "female". Defaults to "female" |

**Output:**
```json
{
  "audio_base64": "<base64-encoded WAV>",
  "format": "wav"
}
```

**Fallback:** Returns empty audio. OpenClaw's Edge TTS with `hi-IN-SwaraNeural` voice handles output speech synthesis, so this tool is primarily useful for Bhashini-native voice quality when available.

---

## Bhashini ULCA Integration

### Two-Step Pipeline

Bhashini uses a two-step authentication and inference flow:

```
Step 1: Get Pipeline Config
POST meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline
Headers: userID, ulcaApiKey
Body: { pipelineTasks, pipelineRequestConfig }
Response: { callbackUrl, inferenceApiKey, serviceId }

Step 2: Run Inference
POST {callbackUrl}
Headers: Authorization: {inferenceApiKey}
Body: { pipelineTasks (with serviceId), inputData }
Response: { pipelineResponse }
```

### Pipeline Config Caching

The Step 1 response (serviceId + callbackUrl) rarely changes, so it's cached in-memory for 1 hour. This avoids an extra round-trip on every tool call.

```python
_pipeline_cache: dict[str, tuple[float, dict]]  # key → (expiry_timestamp, config)
_PIPELINE_TTL = 3600.0  # 1 hour
```

### Auth Headers

```
userID: $BHASHINI_ULCA_USER_ID
ulcaApiKey: $BHASHINI_ULCA_API_KEY
```

Both are set via environment variables. Free PoC tier available at [bhashini.gov.in/ulca](https://bhashini.gov.in/ulca).

---

## Fallback Chain

```
                    ┌─────────────────┐
                    │  Bhashini ULCA  │ ← Primary provider
                    └────────┬────────┘
                             │ failure?
                    ┌────────▼────────┐
              ┌─────┤   Fallback?     ├─────┐
              │     └─────────────────┘     │
         ASR  │          NMT │         TTS  │
              ▼              ▼              ▼
    ┌─────────────┐  ┌──────────────┐  ┌─────────┐
    │   OpenAI    │  │ Pass-through │  │  Empty   │
    │   Whisper   │  │ (return as-  │  │ (Edge    │
    │   API       │  │  is, LLM     │  │  TTS     │
    │             │  │  handles it) │  │  handles │
    └─────────────┘  └──────────────┘  │  output) │
                                       └─────────┘
```

**Why this works:**
- Claude Sonnet understands Hindi natively, so even without translation, the agent can process Hindi text
- OpenClaw's Edge TTS with `hi-IN-SwaraNeural` produces high-quality Hindi speech
- Whisper is a proven fallback for ASR with good Hindi support

---

## Error Handling

- All Bhashini HTTP calls have a **10-second timeout** (httpx)
- Errors trigger fallback providers, not exceptions
- If both primary and fallback fail, tools return structured error data:
  ```json
  {"text": "", "detected_lang": "hi", "error": "Connection timeout"}
  ```
- The LLM agent receives this and can inform the user gracefully

---

## Running

```bash
# Install
cd sahayak/bhashini-lang
pip install -e ".[dev]"

# Run as MCP server (stdio)
python -m bhashini_lang.server

# Run tests
python -m pytest tests/ -v
```
