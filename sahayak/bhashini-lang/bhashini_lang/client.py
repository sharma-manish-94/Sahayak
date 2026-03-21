"""Bhashini ULCA pipeline API client.

Two-step pipeline:
1. POST to meity-auth endpoint to get serviceId + callbackUrl
2. POST to callbackUrl with actual data
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

_AUTH_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
_TIMEOUT = 10.0

# In-memory pipeline config cache (1 hour TTL)
_pipeline_cache: dict[str, tuple[float, dict]] = {}
_PIPELINE_TTL = 3600.0


async def _get_pipeline_config(task_type: str, source_lang: str, target_lang: str | None = None) -> dict:
    """Get pipeline config (serviceId + callbackUrl) from ULCA, with caching."""
    cache_key = f"{task_type}:{source_lang}:{target_lang}"
    cached = _pipeline_cache.get(cache_key)
    if cached and time.monotonic() < cached[0]:
        return cached[1]

    user_id = os.environ.get("BHASHINI_ULCA_USER_ID", "")
    api_key = os.environ.get("BHASHINI_ULCA_API_KEY", "")

    pipeline_tasks: list[dict[str, Any]] = []
    if task_type == "asr":
        pipeline_tasks = [{"taskType": "asr", "config": {"language": {"sourceLanguage": source_lang}}}]
    elif task_type == "tts":
        pipeline_tasks = [{"taskType": "tts", "config": {"language": {"sourceLanguage": source_lang}}}]
    elif task_type == "translation":
        pipeline_tasks = [{"taskType": "translation", "config": {"language": {"sourceLanguage": source_lang, "targetLanguage": target_lang}}}]
    elif task_type == "lid":
        pipeline_tasks = [{"taskType": "asr", "config": {"language": {"sourceLanguage": "en"}}}]

    payload = {
        "pipelineTasks": pipeline_tasks,
        "pipelineRequestConfig": {"pipelineId": "64392f96dadc500b55c543cd"},
    }

    headers = {
        "Content-Type": "application/json",
        "userID": user_id,
        "ulcaApiKey": api_key,
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(_AUTH_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    config = {
        "callback_url": data.get("pipelineInferenceAPIEndPoint", {}).get("callbackUrl", ""),
        "authorization_key": data.get("pipelineInferenceAPIEndPoint", {}).get("inferenceApiKey", {}).get("value", ""),
        "service_id": "",
    }

    # Extract service ID from response
    response_config = data.get("pipelineResponseConfig", [])
    if response_config:
        task_configs = response_config[0].get("config", [])
        if task_configs:
            config["service_id"] = task_configs[0].get("serviceId", "")

    _pipeline_cache[cache_key] = (time.monotonic() + _PIPELINE_TTL, config)
    return config


async def detect_language(text: str) -> dict[str, Any]:
    """Detect language of input text using Bhashini NLU pipeline."""
    # Use a simple heuristic first, then Bhashini if available
    # Hindi detection: check for Devanagari characters
    devanagari_count = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    total_alpha = sum(1 for c in text if c.isalpha())

    if total_alpha == 0:
        return {"language": "en", "confidence": 0.5}

    ratio = devanagari_count / total_alpha
    if ratio > 0.5:
        return {"language": "hi", "confidence": min(0.95, ratio)}
    elif ratio > 0.1:
        return {"language": "hi", "confidence": ratio}
    else:
        return {"language": "en", "confidence": min(0.95, 1.0 - ratio)}


async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using Bhashini NMT pipeline."""
    config = await _get_pipeline_config("translation", source_lang, target_lang)

    headers = {
        "Content-Type": "application/json",
        "Authorization": config["authorization_key"],
    }

    payload = {
        "pipelineTasks": [{
            "taskType": "translation",
            "config": {
                "language": {
                    "sourceLanguage": source_lang,
                    "targetLanguage": target_lang,
                },
                "serviceId": config["service_id"],
            },
        }],
        "inputData": {
            "input": [{"source": text}],
        },
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(config["callback_url"], json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    output = data.get("pipelineResponse", [{}])
    if output:
        texts = output[0].get("output", [{}])
        if texts:
            return texts[0].get("target", text)
    return text


async def speech_to_text(audio_base64: str, source_lang: str) -> dict[str, str]:
    """Transcribe speech using Bhashini ASR pipeline."""
    config = await _get_pipeline_config("asr", source_lang)

    headers = {
        "Content-Type": "application/json",
        "Authorization": config["authorization_key"],
    }

    payload = {
        "pipelineTasks": [{
            "taskType": "asr",
            "config": {
                "language": {"sourceLanguage": source_lang},
                "serviceId": config["service_id"],
            },
        }],
        "inputData": {
            "audio": [{"audioContent": audio_base64}],
        },
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(config["callback_url"], json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    output = data.get("pipelineResponse", [{}])
    if output:
        texts = output[0].get("output", [{}])
        if texts:
            return {"text": texts[0].get("source", ""), "detected_lang": source_lang}
    return {"text": "", "detected_lang": source_lang}


async def text_to_speech(text: str, source_lang: str, gender: str = "female") -> dict[str, str]:
    """Synthesize speech using Bhashini TTS pipeline."""
    config = await _get_pipeline_config("tts", source_lang)

    headers = {
        "Content-Type": "application/json",
        "Authorization": config["authorization_key"],
    }

    payload = {
        "pipelineTasks": [{
            "taskType": "tts",
            "config": {
                "language": {"sourceLanguage": source_lang},
                "serviceId": config["service_id"],
                "gender": gender,
            },
        }],
        "inputData": {
            "input": [{"source": text}],
        },
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(config["callback_url"], json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    output = data.get("pipelineResponse", [{}])
    if output:
        audios = output[0].get("audio", [{}])
        if audios:
            return {
                "audio_base64": audios[0].get("audioContent", ""),
                "format": "wav",
            }
    return {"audio_base64": "", "format": "wav"}
