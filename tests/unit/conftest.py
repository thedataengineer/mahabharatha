"""Shared fixtures for unit tests."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _bypass_rush_preflight():
    """Auto-patch kurukshetra preflight for all unit tests.

    Kurukshetra command tests use mocked MahabharathaConfig whose ports attributes are
    MagicMock objects, causing PreflightChecker to fail on port binding.
    Since preflight is tested separately in test_preflight.py, bypass it here.
    """
    with patch("mahabharatha.commands.kurukshetra._run_preflight", return_value=True):
        yield
