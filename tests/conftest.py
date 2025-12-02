"""
Pytest configuration and fixtures for cv-cue-api tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import tempfile


@pytest.fixture
def mock_client():
    """Create a mock CVCueClient for testing resources."""
    client = Mock()
    client.request = MagicMock()
    client.base_url = "https://test.api.com"
    client.session = MagicMock()
    return client


@pytest.fixture
def temp_session_file():
    """Create a temporary session file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".session") as f:
        temp_path = Path(f.name)
    yield temp_path
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set mock environment variables for CVCueClient."""
    monkeypatch.setenv("CV_CUE_KEY_ID", "env-test-key-id")
    monkeypatch.setenv("CV_CUE_KEY_VALUE", "env-test-key-value")
    monkeypatch.setenv("CV_CUE_CLIENT_ID", "env-test-client")
    monkeypatch.setenv("CV_CUE_BASE_URL", "https://env-test.api.com/api")


@pytest.fixture
def sample_managed_devices_response():
    """Sample API response for managed devices list."""
    return {
        "managedDevices": [
            {
                "boxid": 123,
                "name": "AP-Test-01",
                "macaddress": "AA:BB:CC:DD:EE:FF",
                "model": "AP-555",
                "active": True,
                "ipaddress": "192.168.1.100",
            },
            {
                "boxid": 124,
                "name": "AP-Test-02",
                "macaddress": "11:22:33:44:55:66",
                "model": "AP-635",
                "active": True,
                "ipaddress": "192.168.1.101",
            },
        ],
        "totalCount": 2,
        "pagingSessionId": "session-123",
    }
