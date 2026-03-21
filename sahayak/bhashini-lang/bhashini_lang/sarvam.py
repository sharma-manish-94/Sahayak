"""Sarvam AI client — sovereign Indian language services.

API docs: https://docs.sarvam.ai
Base URL: https://api.sarvam.ai
Auth: api-subscription-key header

Services used:
- /text-lid — language detection
- /translate — translation (Mayura / Sarvam Translate)
- /speech-to-text — ASR (Saarika v2.5 / Saaras v3)
- /text-to-speech — TTS (Bulbul v3)
"""

from __future__ import annotations

import base64
import os
import tempfile
from typing import Any

import httpx

_BASE_URL = "https://api.sarvam.ai"
_TIMEOUT = 15.0

# Language code mapping: ISO 639-1 → Sarvam BCP-47
_LANG_MAP = {
    "hi": "hi-IN",
    "en": "en-IN",
    "bn": "bn-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "mr": "mr-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "pa": "pa-IN",
    "or": "od-IN",
    "od": "od-IN",
    "as": "as-IN",
    "ur": "ur-IN",
}

# Reverse mapping: Sarvam BCP-47 → ISO 639-1
_LANG_MAP_REV = {v: k for k, v in _LANG_MAP.items()}


def _to_sarvam_lang(lang: str) -> str:
    """Convert ISO 639-1 code to Sarvam BCP-47 format."""
    if "-" in lang:
        return lang  # Already BCP-47
    return _LANG_MAP.get(lang, f"{lang}-IN")


def _from_sarvam_lang(lang: str) -> str:
    """Convert Sarvam BCP-47 to ISO 639-1 code."""
    if lang in _LANG_MAP_REV:
        return _LANG_MAP_REV[lang]
    return lang.split("-")[0]


def _get_api_key() -> str:
    return os.environ.get("SARVAM_API_KEY", "")


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "api-subscription-key": _get_api_key(),
    }


async def detect_language(text: str) -> dict[str, Any]:
    """Detect language using Sarvam text-lid endpoint."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_BASE_URL}/text-lid",
            headers=_headers(),
            json={"input": text},
        )
        resp.raise_for_status()
        data = resp.json()

    lang_code = data.get("language_code", "en-IN")
    return {
        "language": _from_sarvam_lang(lang_code),
        "confidence": 0.9,  # Sarvam doesn't return confidence, assume high
        "script": data.get("script_code", ""),
    }


async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using Sarvam Translate API."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_BASE_URL}/translate",
            headers=_headers(),
            json={
                "input": text,
                "source_language_code": _to_sarvam_lang(source_lang),
                "target_language_code": _to_sarvam_lang(target_lang),
                "model": "mayura:v1",
                "mode": "colloquial",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    return data.get("translated_text", text)


async def speech_to_text(audio_base64: str, source_lang: str) -> dict[str, str]:
    """Transcribe speech using Sarvam ASR (Saaras v3)."""
    audio_bytes = base64.b64decode(audio_base64)

    # Sarvam STT expects multipart form-data with a file upload
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(tmp_path, "rb") as audio_file:
                resp = await client.post(
                    f"{_BASE_URL}/speech-to-text",
                    headers={"api-subscription-key": _get_api_key()},
                    data={
                        "model": "saaras:v3",
                        "language_code": _to_sarvam_lang(source_lang),
                    },
                    files={"file": ("audio.ogg", audio_file, "audio/ogg")},
                )
                resp.raise_for_status()
                data = resp.json()

        transcript = data.get("transcript", "")
        detected = data.get("language_code", _to_sarvam_lang(source_lang))
        return {"text": transcript, "detected_lang": _from_sarvam_lang(detected)}
    finally:
        os.unlink(tmp_path)


async def text_to_speech(text: str, source_lang: str, gender: str = "female") -> dict[str, str]:
    """Synthesize speech using Sarvam TTS (Bulbul v3)."""
    # Pick a speaker voice based on language and gender
    speaker = _pick_speaker(source_lang, gender)

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_BASE_URL}/text-to-speech",
            headers=_headers(),
            json={
                "text": text,
                "target_language_code": _to_sarvam_lang(source_lang),
                "speaker": speaker,
                "model": "bulbul:v3",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    # Sarvam returns audios as base64 array
    audios = data.get("audios", [])
    if audios:
        return {"audio_base64": audios[0], "format": "wav"}
    return {"audio_base64": "", "format": "wav"}


def _pick_speaker(lang: str, gender: str) -> str:
    """Pick a Sarvam speaker voice based on language and gender preference."""
    # Sarvam has named speakers; these are common defaults
    female_speakers = {
        "hi": "meera",
        "en": "meera",
        "bn": "meera",
        "ta": "meera",
        "te": "meera",
    }
    male_speakers = {
        "hi": "arvind",
        "en": "arvind",
        "bn": "arvind",
        "ta": "arvind",
        "te": "arvind",
    }

    if gender == "male":
        return male_speakers.get(lang, "arvind")
    return female_speakers.get(lang, "meera")
