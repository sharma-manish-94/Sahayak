"""bhashini-lang MCP server — exposes Indian language tools.

Provider selection via LANG_PROVIDER env var:
  - "sarvam"   → Sarvam AI (sovereign, recommended)
  - "bhashini"  → Bhashini ULCA (default)
  - "auto"      → Sarvam if SARVAM_API_KEY is set, else Bhashini

Fallback chain: primary provider → Whisper (ASR) / passthrough (NMT) / empty (TTS)
"""

from __future__ import annotations

import os

from fastmcp import FastMCP

from . import client as bhashini_client
from . import sarvam as sarvam_client
from . import fallback
from .types import LanguageDetection, TranslationResult, SpeechToTextResult, TextToSpeechResult


def _get_provider():
    """Resolve which language provider to use."""
    provider = os.environ.get("LANG_PROVIDER", "auto").lower()
    if provider == "sarvam":
        return sarvam_client
    if provider == "bhashini":
        return bhashini_client
    # auto: prefer Sarvam if key is set
    if os.environ.get("SARVAM_API_KEY"):
        return sarvam_client
    return bhashini_client


mcp = FastMCP(
    "bhashini-lang",
    instructions="Indian language services — detection, translation, ASR, TTS. Supports Sarvam AI and Bhashini ULCA providers.",
)


@mcp.tool()
async def detect_language(text: str) -> dict:
    """Detect the language of input text. Returns language code and confidence.

    Args:
        text: The text to detect language for
    """
    provider = _get_provider()
    result = await provider.detect_language(text)
    return LanguageDetection(
        language=result["language"],
        confidence=result.get("confidence", 0.9),
    ).model_dump()


@mcp.tool()
async def translate(text: str, source_lang: str, target_lang: str) -> dict:
    """Translate text between Indian languages and English.

    Args:
        text: Text to translate
        source_lang: Source language code — "hi" (Hindi), "en" (English), "bn" (Bengali), "ta" (Tamil), etc.
        target_lang: Target language code
    """
    provider = _get_provider()
    try:
        translated = await provider.translate_text(text, source_lang, target_lang)
    except Exception:
        # Fallback: try the other provider
        other = sarvam_client if provider is bhashini_client else bhashini_client
        try:
            translated = await other.translate_text(text, source_lang, target_lang)
        except Exception:
            translated = await fallback.passthrough_translate(text, source_lang, target_lang)

    return TranslationResult(
        translated_text=translated,
        source_lang=source_lang,
        target_lang=target_lang,
    ).model_dump()


@mcp.tool()
async def speech_to_text(audio_base64: str, source_lang: str | None = None) -> dict:
    """Transcribe speech audio to text.

    Args:
        audio_base64: Base64-encoded audio data (OGG/WAV)
        source_lang: Expected language code, e.g. "hi". If None, defaults to Hindi.
    """
    lang = source_lang or "hi"
    provider = _get_provider()
    try:
        result = await provider.speech_to_text(audio_base64, lang)
    except Exception:
        # Fallback: try other provider, then Whisper
        other = sarvam_client if provider is bhashini_client else bhashini_client
        try:
            result = await other.speech_to_text(audio_base64, lang)
        except Exception:
            result = await fallback.whisper_transcribe(audio_base64, lang)

    return SpeechToTextResult(
        text=result.get("text", ""),
        detected_lang=result.get("detected_lang", lang),
    ).model_dump()


_TTS_MAX_CHARS = 500


@mcp.tool()
async def text_to_speech(text: str, target_lang: str = "hi", gender: str = "female") -> dict:
    """Convert text to speech audio.

    Args:
        text: Text to synthesize (truncated to 500 chars if longer)
        target_lang: Language code, e.g. "hi" for Hindi
        gender: Voice gender — "male" or "female"
    """
    if len(text) > _TTS_MAX_CHARS:
        text = text[:_TTS_MAX_CHARS].rsplit(" ", 1)[0] + "..."

    provider = _get_provider()
    try:
        result = await provider.text_to_speech(text, target_lang, gender)
    except Exception:
        other = sarvam_client if provider is bhashini_client else bhashini_client
        try:
            result = await other.text_to_speech(text, target_lang, gender)
        except Exception:
            result = fallback.empty_tts()

    return TextToSpeechResult(
        audio_base64=result.get("audio_base64", ""),
        format=result.get("format", "wav"),
    ).model_dump()


if __name__ == "__main__":
    mcp.run()
