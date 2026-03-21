"""Shared fixtures for govdata-india tests."""

from __future__ import annotations

import pytest


@pytest.fixture()
def mock_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set a dummy API key for tests."""
    monkeypatch.setenv("DATA_GOV_IN_API_KEY", "test-key-000")
