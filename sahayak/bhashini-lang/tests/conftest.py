"""Shared fixtures for bhashini-lang tests."""

from __future__ import annotations

import pytest


@pytest.fixture()
def mock_bhashini_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set dummy Bhashini credentials for tests."""
    monkeypatch.setenv("BHASHINI_ULCA_USER_ID", "test-user")
    monkeypatch.setenv("BHASHINI_ULCA_API_KEY", "test-key")
