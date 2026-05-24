"""
pytest configuration for integration tests against the deployed backend.

This configuration is used when running tests against https://dadn.dungne.io.vn
instead of a local development server.

Environment Variables:
  TEST_AUTH_TOKEN    - JWT token for authentication (if not set, tests will fail auth checks)
  TEST_BACKEND_URL   - Backend URL (defaults to https://dadn.dungne.io.vn)
"""

import os
import pytest
from requests.auth import HTTPBasicAuth

# Configuration
BACKEND_URL = os.getenv("TEST_BACKEND_URL", "https://dadn.dungne.io.vn")
AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN", "")


@pytest.fixture
def auth_token():
    """Provide JWT auth token for tests."""
    if not AUTH_TOKEN:
        pytest.skip("TEST_AUTH_TOKEN not set in environment")
    return AUTH_TOKEN


@pytest.fixture
def auth_headers(auth_token):
    """Provide authorization headers for HTTP requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def base_url():
    """Provide the backend base URL."""
    return BACKEND_URL


def pytest_configure(config):
    """Print configuration info at test start."""
    if not AUTH_TOKEN:
        print("\n⚠️  TEST_AUTH_TOKEN environment variable not set.")
        print("Set it to run authenticated tests:")
        print("   export TEST_AUTH_TOKEN='your-jwt-token'")
        print("Or use: pytest --tb=short -v -k 'test_no_auth'\n")
