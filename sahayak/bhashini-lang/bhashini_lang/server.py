"""bhashini-lang MCP server — exposes Bhashini language tools."""

from __future__ import annotations

from fastmcp import FastMCP

from . import client, fallback
from .types import LanguageDetection, TranslationResult, SpeechToTextResult, TextToSpeechResult

mcp = FastMCP(
    "bhashini-lang",
    instructions="Bhashini language services — detection, translation, ASR, TTS for Indian languages",
)


@mcp.tool()
async def detect_language(text: str) -> dict:
    """Detect the language of input text. Returns language code and confidence.

    Args:
        text: The text to detect language for
    """
    result = await client.detect_language(text)
    return LanguageDetection(**result).model_dump()


@mcp.tool()
async def translate(text: str, source_lang: str, target_lang: str) -> dict:
    """Translate text between Indian languages and English.

    Args:
        text: Text to translate
        source_lang: Source language code — "hi" (Hindi), "en" (English), "bn" (Bengali), "ta" (Tamil), etc.
        target_lang: Target language code
    """
    try:
        translated = await client.translate_text(text, source_lang, target_lang)
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
    try:
        result = await client.speech_to_text(audio_base64, lang)
    except Exception:
        result = await fallback.whisper_transcribe(audio_base64, lang)

    return SpeechToTextResult(
        text=result.get("text", ""),
        detected_lang=result.get("detected_lang", lang),
    ).model_dump()


@mcp.tool()
async def text_to_speech(text: str, target_lang: str = "hi", gender: str = "female") -> dict:
    """Convert text to speech audio.

    Args:
        text: Text to synthesize
        target_lang: Language code, e.g. "hi" for Hindi
        gender: Voice gender — "male" or "female"
    """
    try:
        result = await client.text_to_speech(text, target_lang, gender)
    except Exception:
        result = fallback.empty_tts()

    return TextToSpeechResult(
        audio_base64=result.get("audio_base64", ""),
        format=result.get("format", "wav"),
    ).model_dump()


if __name__ == "__main__":
    mcp.run()
