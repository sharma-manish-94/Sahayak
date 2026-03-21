"""Tests for bhashini-lang MCP server tools."""

from __future__ import annotations

import pytest
import httpx
import respx

from bhashini_lang.client import detect_language, _pipeline_cache


class TestDetectLanguage:
    @pytest.mark.asyncio
    async def test_detect_hindi(self):
        result = await detect_language("नमस्ते, मुझे मंडी भाव बताओ")
        assert result["language"] == "hi"
        assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_detect_english(self):
        result = await detect_language("What is the weather in Bhopal?")
        assert result["language"] == "en"
        assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_detect_mixed(self):
        # Hinglish — should still detect something
        result = await detect_language("PM KISAN status batao")
        assert result["language"] in ("hi", "en")

    @pytest.mark.asyncio
    async def test_detect_empty(self):
        result = await detect_language("12345")
        assert "language" in result


class TestTranslate:
    @pytest.mark.asyncio
    @respx.mock
    async def test_translate_with_bhashini(self, mock_bhashini_env):
        _pipeline_cache.clear()

        # Mock pipeline config request
        respx.post("https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline").mock(
            return_value=httpx.Response(200, json={
                "pipelineInferenceAPIEndPoint": {
                    "callbackUrl": "https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
                    "inferenceApiKey": {"value": "test-inference-key"},
                },
                "pipelineResponseConfig": [
                    {"config": [{"serviceId": "ai4bharat/nmt-en-hi"}]}
                ],
            })
        )

        # Mock translation request
        respx.post("https://dhruva-api.bhashini.gov.in/services/inference/pipeline").mock(
            return_value=httpx.Response(200, json={
                "pipelineResponse": [
                    {"output": [{"target": "नमस्ते दुनिया"}]}
                ],
            })
        )

        from bhashini_lang.client import translate_text
        result = await translate_text("Hello world", "en", "hi")
        assert result == "नमस्ते दुनिया"


class TestSpeechToText:
    @pytest.mark.asyncio
    @respx.mock
    async def test_stt_with_bhashini(self, mock_bhashini_env):
        _pipeline_cache.clear()

        respx.post("https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline").mock(
            return_value=httpx.Response(200, json={
                "pipelineInferenceAPIEndPoint": {
                    "callbackUrl": "https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
                    "inferenceApiKey": {"value": "test-key"},
                },
                "pipelineResponseConfig": [
                    {"config": [{"serviceId": "ai4bharat/asr-hi"}]}
                ],
            })
        )

        respx.post("https://dhruva-api.bhashini.gov.in/services/inference/pipeline").mock(
            return_value=httpx.Response(200, json={
                "pipelineResponse": [
                    {"output": [{"source": "गेहूं का भाव बताओ"}]}
                ],
            })
        )

        from bhashini_lang.client import speech_to_text
        result = await speech_to_text("dGVzdA==", "hi")  # base64 "test"
        assert result["text"] == "गेहूं का भाव बताओ"
