"""Pydantic models for bhashini-lang MCP responses."""

from __future__ import annotations

from pydantic import BaseModel


class LanguageDetection(BaseModel):
    language: str
    confidence: float


class TranslationResult(BaseModel):
    translated_text: str
    source_lang: str
    target_lang: str


class SpeechToTextResult(BaseModel):
    text: str
    detected_lang: str


class TextToSpeechResult(BaseModel):
    audio_base64: str
    format: str = "wav"
