"""
Tests for CVCueClient class.
"""

import pytest
import pickle
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from cv_cue_api.cv_cue_client import CVCueClient


class TestCVCueClientInitialization:
    """Test CVCueClient initialization."""

    def test_init_with_parameters(self, monkeypatch, temp_session_file):
        """Test initialization with explicit parameters (should override env vars)."""
        # Ensure temp session file doesn't exist
        if temp_session_file.exists():
            temp_session_file.unlink()

        # Set environment variables to different values
        monkeypatch.setenv("CV_CUE_KEY_ID", "env-test-key-id")
        monkeypatch.setenv("CV_CUE_KEY_VALUE", "env-test-key-value")
        monkeypatch.setenv("CV_CUE_CLIENT_ID", "env-test-client")
        monkeypatch.setenv("CV_CUE_BASE_URL", "https://env-test.api.com/api")

        # Pass parameters - these should take precedence
        client = CVCueClient(
            key_id="param-test-key",
            key_value="param-test-value",
            client_id="param-test-client",
            base_url="https://param-test.api.com",
            session_file=temp_session_file
        )

        # Verify params were used, not env vars
        assert client.key_id == "param-test-key"
        assert client.key_value == "param-test-value"
        assert client.client_id == "param-test-client"
        assert client.base_url == "https://param-test.api.com"
        assert client.session_file == temp_session_file

    def test_init_with_env_vars(self, mock_env_vars, temp_session_file):
        """Test initialization with environment variables (no params passed)."""
        # Ensure temp session file doesn't exist
        if temp_session_file.exists():
            temp_session_file.unlink()

        # Don't pass any parameters - should load from env vars
        client = CVCueClient(session_file=temp_session_file)

        # Verify env vars were used
        assert client.key_id == "env-test-key-id"
        assert client.key_value == "env-test-key-value"
        assert client.client_id == "env-test-client"
        assert client.base_url == "https://env-test.api.com/api"

    def test_init_missing_credentials(self, temp_session_file, monkeypatch):
        """Test that missing credentials raises ValueError."""
        # Ensure temp session file doesn't exist
        if temp_session_file.exists():
            temp_session_file.unlink()

        # Clear any environment variables that might interfere
        monkeypatch.delenv("CV_CUE_KEY_ID", raising=False)
        monkeypatch.delenv("CV_CUE_KEY_VALUE", raising=False)
        monkeypatch.delenv("CV_CUE_CLIENT_ID", raising=False)
        monkeypatch.delenv("CV_CUE_BASE_URL", raising=False)

        # Test missing key_id
        with pytest.raises(ValueError, match="CV-CUE API key ID"):
            CVCueClient(key_value="value", client_id="client", session_file=temp_session_file)

        # Test missing key_value
        with pytest.raises(ValueError, match="CV-CUE API key value"):
            CVCueClient(key_id="id", client_id="client", session_file=temp_session_file)

        # Test missing client_id
        with pytest.raises(ValueError, match="CV-CUE client ID"):
            CVCueClient(key_id="id", key_value="value", session_file=temp_session_file)

    def test_base_url_trailing_slash_removed(self, temp_session_file):
        """Test that trailing slash is removed from base_url."""
        # Ensure temp session file doesn't exist
        if temp_session_file.exists():
            temp_session_file.unlink()

        client = CVCueClient(
            key_id="test", key_value="test", client_id="test",
            base_url="https://test.api.com/",
            session_file=temp_session_file
        )

        assert client.base_url == "https://test.api.com"

    def test_resource_cache_initialized(self, mock_env_vars, temp_session_file):
        """Test that resource cache is initialized."""
        # Ensure temp session file doesn't exist
        if temp_session_file.exists():
            temp_session_file.unlink()

        client = CVCueClient(session_file=temp_session_file)
        assert hasattr(client, '_resource_cache')
        assert isinstance(client._resource_cache, dict)
        assert len(client._resource_cache) == 0


class TestCVCueClientSessionManagement:
    """Test session management methods."""

    def test_load_session_nonexistent_file(self, mock_env_vars, temp_session_file):
        """Test loading session when file doesn't exist."""
        # Ensure file doesn't exist
        if temp_session_file.exists():
            temp_session_file.unlink()

        client = CVCueClient(session_file=temp_session_file)
        # Should not raise error, just have no cookies
        assert len(client.session.cookies) == 0

    def test_save_and_load_session(self, mock_env_vars, temp_session_file):
        """Test saving and loading session cookies."""
        # Ensure temp session file doesn't exist initially
        if temp_session_file.exists():
            temp_session_file.unlink()

        client = CVCueClient(session_file=temp_session_file)

        # Add a cookie to the session
        client.session.cookies.set('JSESSIONID', 'test-session-id')

        # Save the session
        client._save_session()

        # Create a new client and verify cookie was loaded
        client2 = CVCueClient(session_file=temp_session_file)
        assert 'JSESSIONID' in client2.session.cookies
        assert client2.session.cookies.get('JSESSIONID') == 'test-session-id'

    def test_clear_session(self, mock_env_vars, temp_session_file):
        """Test clearing session file."""
        # Ensure temp session file doesn't exist initially
        if temp_session_file.exists():
            temp_session_file.unlink()

        client = CVCueClient(session_file=temp_session_file)

        # Create and save a session
        client.session.cookies.set('JSESSIONID', 'test-session-id')
        client._save_session()
        assert temp_session_file.exists()

        # Clear session
        client.clear_session()
        assert not temp_session_file.exists()

    @patch('cv_cue_api.cv_cue_client.pickle.load')
    def test_load_session_corrupted_file(self, mock_pickle_load, mock_env_vars, temp_session_file):
        """Test loading corrupted session file."""
        # Create a file
        temp_session_file.touch()

        # Make pickle.load raise an exception
        mock_pickle_load.side_effect = Exception("Corrupted file")

        # Should handle the error gracefully
        client = CVCueClient(session_file=temp_session_file)

        # File should have been deleted
        assert not temp_session_file.exists()


class TestCVCueClientSessionValidation:
    """Test session validation methods."""

    def test_is_session_active_no_cookie(self, mock_env_vars, temp_session_file):
        """Test is_session_active when JSESSIONID cookie is missing."""
        # Ensure temp session file doesn't exist
        if temp_session_file.exists():
            temp_session_file.unlink()

        client = CVCueClient(session_file=temp_session_file)
        assert not client.is_session_active()

    @patch('requests.Session.get')
    def test_is_session_active_valid_session(self, mock_get, mock_env_vars, temp_session_file):
        """Test is_session_active with valid session."""
        # Ensure temp session file doesn't exist
        if temp_session_file.exists():
            temp_session_file.unlink()

        client = CVCueClient(session_file=temp_session_file)
        client.session.cookies.set('JSESSIONID', 'test-session-id')

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert client.is_session_active() is True

    @patch('requests.Session.get')
    def test_is_session_active_invalid_session(self, mock_get, mock_env_vars, temp_session_file):
        """Test is_session_active with invalid session."""
        # Ensure temp session file doesn't exist
        if temp_session_file.exists():
            temp_session_file.unlink()

        client = CVCueClient(session_file=temp_session_file)
        client.session.cookies.set('JSESSIONID', 'invalid-session-id')

        # Mock API response with 401
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        assert client.is_session_active() is False


class TestCVCueClientLogin:
    """Test login functionality."""

    @patch('cv_cue_api.cv_cue_client.CVCueClient.request')
    def test_login_success(self, mock_request, mock_env_vars, temp_session_file):
        """Test successful login."""
        # Ensure temp session file doesn't exist
        if temp_session_file.exists():
            temp_session_file.unlink()

        mock_request.return_value = {"status": "success", "sessionId": "12345"}

        client = CVCueClient(session_file=temp_session_file)

        # Mock the session cookie being set
        client.session.cookies.set('JSESSIONID', 'new-session-id')

        result = client.login()

        # Verify login request was made
        mock_request.assert_called_once()
        call_args = mock_request.call_args

        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/session"
        assert "json" in call_args[1]

        login_data = call_args[1]["json"]
        assert login_data["type"] == "apiKeyCredentials"
        assert login_data["keyId"] == "env-test-key-id"
        assert login_data["keyValue"] == "env-test-key-value"
        assert login_data["clientIdentifier"] == "env-test-client"
        assert login_data["timeout"] == 300

        # Verify session was saved
        assert temp_session_file.exists()


class TestCVCueClientRequest:
    """Test request method."""

    @patch('requests.Session.request')
    def test_request_get(self, mock_session_request, mock_env_vars, temp_session_file):
        """Test GET request."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_session_request.return_value = mock_response

        client = CVCueClient(session_file=temp_session_file)
        result = client.request("GET", "/test", params={"key": "value"})

        assert result == {"data": "test"}
        mock_session_request.assert_called_once()

        call_args = mock_session_request.call_args
        assert call_args[0][0] == "GET"
        assert "test.api.com/api/test" in call_args[0][1]
        assert call_args[1]["params"] == {"key": "value"}

    @patch('requests.Session.request')
    def test_request_post_with_json(self, mock_session_request, mock_env_vars, temp_session_file):
        """Test POST request with JSON data."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_session_request.return_value = mock_response

        client = CVCueClient(session_file=temp_session_file)
        result = client.request("POST", "/test", json={"key": "value"})

        assert result == {"success": True}
        call_args = mock_session_request.call_args
        assert call_args[1]["json"] == {"key": "value"}

    @patch('requests.Session.request')
    def test_request_content_type_header(self, mock_session_request, mock_env_vars, temp_session_file):
        """Test that Content-Type header is added when no json data."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_session_request.return_value = mock_response

        client = CVCueClient(session_file=temp_session_file)
        client.request("GET", "/test")

        call_args = mock_session_request.call_args
        assert "headers" in call_args[1]
        assert call_args[1]["headers"]["Content-Type"] == "application/json"


class TestCVCueClientResourceRegistry:
    """Test resource registry functionality."""

    def test_register_resource(self):
        """Test registering a resource."""
        from cv_cue_api.resources.base import BaseResource

        # Create a test resource
        @BaseResource.register('test_resource')
        class TestResource(BaseResource):
            pass

        # Verify it was registered
        assert 'test_resource' in CVCueClient._resource_registry
        assert CVCueClient._resource_registry['test_resource'] == TestResource

    def test_access_registered_resource(self, mock_env_vars, temp_session_file):
        """Test accessing a registered resource."""
        client = CVCueClient(session_file=temp_session_file)

        # Access managed_devices resource (should be registered)
        md = client.managed_devices

        # Verify it's a resource instance
        assert md is not None
        assert hasattr(md, 'client')
        assert md.client == client

    def test_resource_caching(self, mock_env_vars, temp_session_file):
        """Test that resources are cached."""
        client = CVCueClient(session_file=temp_session_file)

        # Access resource twice
        md1 = client.managed_devices
        md2 = client.managed_devices

        # Should be the same instance
        assert md1 is md2

    def test_access_unregistered_resource(self, mock_env_vars, temp_session_file):
        """Test accessing an unregistered resource raises AttributeError."""
        client = CVCueClient(session_file=temp_session_file)

        with pytest.raises(AttributeError, match="no resource"):
            _ = client.nonexistent_resource


class TestCVCueClientContextManager:
    """Test context manager functionality."""

    def test_context_manager(self, mock_env_vars, temp_session_file):
        """Test using client as context manager."""
        with CVCueClient(session_file=temp_session_file) as client:
            assert client.session is not None

        # Session should be closed after exiting context
        # (Hard to test directly, but at least verify no errors)

    @patch('cv_cue_api.cv_cue_client.CVCueClient.close')
    def test_context_manager_calls_close(self, mock_close, mock_env_vars, temp_session_file):
        """Test that context manager calls close."""
        with CVCueClient(session_file=temp_session_file) as client:
            pass

        mock_close.assert_called_once()
