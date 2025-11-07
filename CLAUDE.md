# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cv-cue-wrapper is a Python SDK and CLI tool for interacting with the CV-CUE API (Arista CloudVision CUE WiFi management platform). It provides both a programmatic interface and a Docker-like command-line tool.

## Development Commands

### Environment Setup
```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run tests with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_filters.py

# Run specific test class
poetry run pytest tests/test_cv_cue_client.py::TestCVCueClientInitialization

# Run specific test method
poetry run pytest tests/test_cv_cue_client.py::TestCVCueClientInitialization::test_init_with_parameters

# Run tests with coverage
poetry run pytest --cov=cv_cue_wrapper
```

### CLI Usage
```bash
# Run CLI directly
poetry run cv-cue-wrapper --help

# Test session management
poetry run cv-cue-wrapper session status
poetry run cv-cue-wrapper session login

# Test managed devices commands
poetry run cv-cue-wrapper managed-devices list-aps --output table
```

## Architecture

### Resource-Based SDK Pattern

This project follows a **resource-based architecture**. Key concepts:

1. **CVCueClient** - Main client class that:
   - Manages HTTP sessions with cookie-based authentication
   - Maintains a registry of API resources
   - Lazy-loads resources on first access (e.g., `client.managed_devices`)
   - Handles session caching in `.session` file

2. **Resource Registration** - Resources register themselves via decorator:
   ```python
   @BaseResource.register('managed_devices')
   class ManagedDevicesResource(BaseResource):
       pass
   ```
   The registration happens at import time, making resources available as attributes on the client.

3. **Session Management**:
   - Sessions use JSESSIONID cookie for authentication
   - Cookies are pickled to `.session` file for persistence
   - `is_session_active()` checks JSESSIONID presence + validates via GET /session
   - `login()` creates session via POST /session with apiKeyCredentials

### Filter System

Advanced filtering uses a builder pattern with operator mapping:

- **Filter Class**: Represents single filter with property, operator, value
- **Operator Mapping**: Friendly names (e.g., "contains", "equals") map to API operators (e.g., "contains", "=")
- **FilterBuilder**: Fluent API for combining multiple filters with AND/OR logic
- Filters serialize to URL-encoded JSON strings when passed to API

Example:
```python
fb = FilterBuilder("AND")
fb.contains("name", "Arista").equals("active", True)
# Produces: filter=[{"property":"name","operator":"contains","value":["Arista"]}, ...]
```

### CLI Structure

The CLI uses Click with hierarchical command groups (Docker-like):
```
cv-cue-wrapper
├── session (login, status, clear)
└── managed-devices (list-aps, get-all-aps)
```

Commands automatically handle:
- Session validation and auto-login
- Multiple output formats (json, table, compact)
- Filter parsing from CLI args (property:operator:value format)

## Key Implementation Details

### Credential Loading Priority
The client loads credentials in this order:
1. Constructor parameters (highest priority)
2. Environment variables (CV_CUE_KEY_ID, CV_CUE_KEY_VALUE, CV_CUE_CLIENT_ID, CV_CUE_BASE_URL)
3. Fails with ValueError if credentials missing

### Request Flow
1. `CVCueClient.request()` - Central request handler
2. Sets Content-Type: application/json header (CV-CUE API requirement)
3. Resources use `_request()` helper that delegates to client
4. Legacy `_make_request()` exists for backwards compatibility

### Test Structure
Tests use pytest with extensive mocking:
- `tests/conftest.py` - Shared fixtures (mock_client, temp_session_file, mock_env_vars)
- Tests verify credential loading from each source independently
- Always clear `temp_session_file` before tests to avoid state pollution
- Use `monkeypatch` for environment variable manipulation

## Adding New Resources

To add a new API resource (e.g., "networks"):

1. Create `cv_cue_wrapper/resources/networks.py`:
   ```python
   from .base import BaseResource

   @BaseResource.register('networks')
   class NetworksResource(BaseResource):
       def list(self, **kwargs):
           return self._request('GET', '/networks', params=kwargs)
   ```

2. Import in `cv_cue_wrapper/resources/__init__.py`:
   ```python
   from .networks import NetworksResource
   __all__ = [..., 'NetworksResource']
   ```

3. Resource is now available as `client.networks.list()`

## Environment Configuration

Required environment variables (or pass to constructor):
```bash
CV_CUE_KEY_ID="KEY-..."
CV_CUE_KEY_VALUE="..."
CV_CUE_CLIENT_ID="..."
CV_CUE_BASE_URL="https://..."  # Optional, defaults to production
```

Use `.env.example` as template. The `.session` file is git-ignored and contains pickled cookies.

## Important Files

- `README.md` - CLI usage guide with examples and command reference
- `cv_cue_wrapper/cv_cue_client.py` - Core client with session management
- `cv_cue_wrapper/resources/filters.py` - Filter and FilterBuilder classes
- `cv_cue_wrapper/resources/managed_devices.py` - Managed devices (access points) resource
- `cv_cue_wrapper/main.py` - Click-based CLI implementation
- `tests/conftest.py` - Test fixtures and configuration
