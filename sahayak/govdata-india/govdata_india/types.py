"""Pydantic models for govdata-india MCP responses."""

from __future__ import annotations

from pydantic import BaseModel


# --- Mandi prices ---

class MandiPrice(BaseModel):
    mandi: str
    commodity: str
    variety: str
    min_price: float
    max_price: float
    modal_price: float
    date: str


class MandiPricesResponse(BaseModel):
    prices: list[MandiPrice]
    source: str = "data.gov.in (Agmarknet)"


# --- PM-KISAN ---

class PMKisanStatus(BaseModel):
    state: str
    district: str
    beneficiary_count: int
    last_installment: str
    amount_per_installment: float


class PMKisanResponse(BaseModel):
    status: PMKisanStatus | None = None
    message: str = ""
    source: str = "data.gov.in (PM-KISAN)"


# --- Weather ---

class WeatherInfo(BaseModel):
    district: str
    state: str
    temp_max: float | None = None
    temp_min: float | None = None
    rainfall: float | None = None
    humidity: float | None = None
    forecast: str = ""
    advisory: str = ""


class WeatherResponse(BaseModel):
    weather: WeatherInfo | None = None
    message: str = ""
    source: str = "IMD / data.gov.in"


# --- Schemes ---

class Scheme(BaseModel):
    name: str
    ministry: str
    benefits: str
    eligibility: str
    how_to_apply: str
    url: str = ""


class SchemesResponse(BaseModel):
    schemes: list[Scheme]
    query: str
    source: str = "Sahayak curated database"
