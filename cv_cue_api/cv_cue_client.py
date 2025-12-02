import os
import pickle
import requests
from pathlib import Path
from .config import logger
from typing import Optional, Type, Dict

class CVCueClient:
    """Client for interacting with the CV/CUE API."""

    # Class-level registry of available resources
    _resource_registry: Dict[str, Type['BaseResource']] = {}

    SESSION_FILE = Path(".session")

    def __init__(self, key_id: Optional[str] = None, key_value: Optional[str] = None, client_id: Optional[str] = None, base_url: Optional[str] = None, session_file: Optional[Path] = None):
        """
        Initialize the CV/CUE API client.

        Args:
            key_id: API key ID for authentication
            key_value: API key value for authentication
            client_id: Client identifier for the session
            base_url: Base URL for the API. If not provided, reads from CV_CUE_BASE_URL env var.
            session_file: Path to session cache file. Defaults to .session in current directory.
        """
        self.key_id = key_id or os.getenv('CV_CUE_KEY_ID')
        self.key_value = key_value or os.getenv('CV_CUE_KEY_VALUE')
        self.client_id = client_id or os.getenv('CV_CUE_CLIENT_ID')
        self.base_url = base_url or os.getenv('CV_CUE_BASE_URL')
        self.session_file = session_file or self.SESSION_FILE

        if not self.key_id:
            raise ValueError("CV-CUE API key ID must be provided or set in CV_CUE_KEY_ID environment variable")
        if not self.key_value:
            raise ValueError("CV-CUE API key value must be provided or set in CV_CUE_KEY_VALUE environment variable")
        if not self.client_id:
            raise ValueError("CV-CUE client ID must be provided or set in CV_CUE_CLIENT_ID environment variable")

        self.base_url = self.base_url.rstrip('/')

        self.session = requests.Session()
        self._load_session()

        # Cache for instantiated resources
        self._resource_cache: Dict[str, 'BaseResource'] = {}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict[str, any]] = None,
        params: Optional[dict[str, any]] = None
    ) -> dict[str, any]:
        """
        Legacy request method - use request() instead.

        This method is kept for backwards compatibility but delegates to request().

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (without base URL)
            data: JSON data to send in request body
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            requests.HTTPError: If the request fails
        """
        path = f"/{endpoint.lstrip('/')}"
        kwargs = {}
        if data is not None:
            kwargs['json'] = data
        if params is not None:
            kwargs['params'] = params

        try:
            return self.request(method, path, **kwargs)
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            logger.error(f"Response content: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def _load_session(self):
        """Load cached session cookies from file if available."""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'rb') as f:
                    cookies = pickle.load(f)
                self.session.cookies.update(cookies)
                logger.info(f"Loaded session from {self.session_file}")
            except Exception as e:
                logger.warning(f"Failed to load session cache: {e}")
                # Remove corrupted session file
                try:
                    self.session_file.unlink()
                except Exception:
                    pass

    def _save_session(self):
        """Save session cookies to cache file."""
        try:
            with open(self.session_file, 'wb') as f:
                pickle.dump(self.session.cookies, f)
            logger.info(f"Saved session to {self.session_file}")
        except Exception as e:
            logger.error(f"Failed to save session cache: {e}")

    def is_session_active(self) -> bool:
        """
        Check if the current session is active.

        First checks if JSESSIONID cookie exists, then validates with GET /session.

        Returns:
            True if session is active (200 response), False otherwise (4xx response or missing cookie)
        """
        # Check if JSESSIONID cookie exists
        if 'JSESSIONID' not in self.session.cookies:
            logger.info("Session is not active: JSESSIONID cookie not found")
            return False

        try:
            url = f"{self.base_url}/session"
            logger.info(f"Checking session status at {url}")
            response = self.session.get(url)

            if response.status_code == 200:
                logger.info("Session is active")
                return True
            else:
                logger.info(f"Session is not active (status: {response.status_code})")
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to check session status: {e}")
            return False

    def login(self):
        """
        Authenticate with the CV-CUE API and cache the session cookies.

        Returns:
            Response JSON data from the login endpoint
        """
        data = {
            "type": "apiKeyCredentials",
            "keyId": self.key_id,
            "keyValue": self.key_value,
            "clientIdentifier": self.client_id,
            "timeout": 300,
        }
        endpoint = 'session'
        response = self._make_request('POST', endpoint, data=data)

        # Save session cookies after successful login
        self._save_session()

        return response

    def get(self, endpoint: str, params: Optional[dict[str, any]] = None) -> dict[str, any]:
        """Make a GET request to the API."""
        return self._make_request('GET', endpoint, params=params)

    def post(self, endpoint: str, data: Optional[dict[str, any]] = None) -> dict[str, any]:
        """Make a POST request to the API."""
        return self._make_request('POST', endpoint, data=data)

    def put(self, endpoint: str, data: Optional[dict[str, any]] = None) -> dict[str, any]:
        """Make a PUT request to the API."""
        return self._make_request('PUT', endpoint, data=data)

    def delete(self, endpoint: str) -> dict[str, any]:
        """Make a DELETE request to the API."""
        return self._make_request('DELETE', endpoint)

    def clear_session(self):
        """Clear cached session file."""
        if self.session_file.exists():
            try:
                self.session_file.unlink()
                logger.info(f"Cleared session cache: {self.session_file}")
            except Exception as e:
                logger.error(f"Failed to clear session cache: {e}")

    @classmethod
    def register_resource(cls, name: str, resource_class: Type['BaseResource']):
        """
        Register a resource class to make it available on the client.

        Args:
            name: The attribute name to access this resource (e.g., 'devices')
            resource_class: The resource class to register
        """
        cls._resource_registry[name] = resource_class

    def __getattr__(self, name: str):
        """
        Lazy-load resources on first access.

        This method is called when accessing an attribute that doesn't exist
        on the instance. It checks if the requested name is a registered
        resource and instantiates it if so.
        """
        # Check cache first
        if name in self._resource_cache:
            return self._resource_cache[name]

        # Check if resource is registered
        if name in self._resource_registry:
            resource_class = self._resource_registry[name]
            resource_instance = resource_class(self)
            self._resource_cache[name] = resource_instance
            return resource_instance

        raise AttributeError(
            f"CVCueClient has no resource '{name}'. "
            f"Available resources: {', '.join(self._resource_registry.keys())}"
        )

    def __dir__(self):
        """
        Make resources discoverable for autocomplete.

        This allows IDEs and the dir() function to show available resources.
        """
        return list(self._resource_registry.keys()) + list(self.__dict__.keys())

    def request(self, method: str, path: str, **kwargs):
        """
        Centralized request handler for all API calls.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE, etc.)
            path: API endpoint path (e.g., '/devices' or '/devices/123')
            **kwargs: Additional arguments passed to requests (params, json, etc.)

        Returns:
            Parsed JSON response

        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}{path}"

        # CV-CUE API requires Content-Type header even for requests without body
        if 'headers' not in kwargs and not kwargs.get('json'):
            kwargs['headers'] = {"Content-Type": "application/json"}

        logger.info(f"Making {method} request to {url}")
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
