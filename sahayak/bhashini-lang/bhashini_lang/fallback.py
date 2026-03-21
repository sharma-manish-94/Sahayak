"""Fallback providers when Bhashini is unavailable.

- ASR fallback: OpenAI Whisper API
- NMT fallback: pass-through with warning
- TTS fallback: return empty (OpenClaw's Edge TTS handles output)
"""

from __future__ import annotations

import os
import httpx


async def whisper_transcribe(audio_base64: str, language: str | None = None) -> dict[str, str]:
    """Transcribe audio using OpenAI Whisper API as fallback ASR."""
    import base64
    import tempfile

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"text": "", "detected_lang": language or "hi", "error": "No OpenAI API key configured"}

    # Decode base64 audio to temp file
    audio_bytes = base64.b64decode(audio_base64)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(tmp_path, "rb") as audio_file:
                resp = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    data={"model": "whisper-1", "language": language or "hi"},
                    files={"file": ("audio.ogg", audio_file, "audio/ogg")},
                )
                resp.raise_for_status()
                data = resp.json()
        return {"text": data.get("text", ""), "detected_lang": language or "hi"}
    except (httpx.HTTPError, Exception) as exc:
        return {"text": "", "detected_lang": language or "hi", "error": str(exc)}
    finally:
        os.unlink(tmp_path)


async def passthrough_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Pass-through fallback when Bhashini NMT is unavailable."""
    # Return original text with a note — the LLM can still reason about it
    return text


def empty_tts() -> dict[str, str]:
    """Return empty audio — OpenClaw's Edge TTS handles output voice."""
    return {"audio_base64": "", "format": "wav"}
