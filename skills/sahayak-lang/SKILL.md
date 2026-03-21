---
name: sahayak-lang
description: Bhashini language services for Indian languages — detection, translation, speech-to-text, text-to-speech
mcp_server: bhashini-lang
---

# Sahayak Language Services

This skill provides multilingual support for Indian languages via the Bhashini ULCA platform.

## Tools

### detect_language
Detect the language of input text. Returns ISO 639-1 code and confidence score.
Use this when you receive text and need to determine if it's Hindi, English, or another Indian language.

### translate
Translate text between Indian languages and English.
Supported languages: hi (Hindi), en (English), bn (Bengali), ta (Tamil), te (Telugu), mr (Marathi), gu (Gujarati), kn (Kannada), ml (Malayalam), pa (Punjabi), or (Odia), as (Assamese), ur (Urdu).

### speech_to_text
Transcribe speech audio (base64-encoded OGG/WAV) to text.
Used automatically when user sends a voice note. Default language is Hindi.

### text_to_speech
Convert text to speech audio (returns base64 WAV).
Use when the response should be delivered as a voice note.

## When to use
- Detecting user's language before responding
- Translating queries or responses between languages
- Processing voice notes from WhatsApp users
- Generating voice responses
