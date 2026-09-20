"""
Pytest Fixture Configuration for Supabase Backend Testing
- Manages environment variable resolution (test.env fallback).
- Provides tiered HTTP request sessions for anonymous, authenticated, 
  and cross-user isolation / RLS boundary testing.
"""

# =====================================================================
# Module Imports & Purpose Ledger
# =====================================================================
import os                    # Runtime environment variable retrieval (SUPABASE_URL, secrets)
from pathlib import Path     # Object-oriented, cross-platform filesystem path navigation
import pytest                # Test runner fixture lifecycle orchestration (@pytest.fixture)
import requests              # Synchronous HTTP client for PostgREST API queries & auth exchanges
from dotenv import load_dotenv  # Injects local .env key-value pairs into os.environ (# type: ignore)

# =====================================================================
# Environment Bootstrap & Validation
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / "test.env"  # Default: root directory relative to /tests

# Fallback: check current directory if project root lookup misses
if not ENV_PATH.exists():
    ENV_PATH = BASE_DIR / "test.env"

# Load environment configuration, overriding existing shell vars if test.env is present
if not os.getenv("SUPABASE_URL") and ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    load_dotenv(override=True)


# =====================================================================
# Core URL & Session Fixtures
# =====================================================================
@pytest.fixture(scope="session")
def base_url():
    """Resolve Supabase PostgREST base endpoint URL."""
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        raise ValueError(
            f"Failed to load SUPABASE_URL. Checked path: {ENV_PATH.resolve()}"
        )
    return f"{supabase_url}/rest/v1"


@pytest.fixture(scope="session")
def api_session():
    """
    Session-scoped HTTP session initialized with Supabase anon key 
    and standard PostgREST representation header.
    """
    session = requests.Session()
    api_key = os.getenv("SUPABASE_ANON_KEY")

    if not api_key:
        raise ValueError("Failed to load SUPABASE_ANON_KEY from environment variables.")

    session.headers.update(
        {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
    )
    yield session
    session.close()


# =====================================================================
# Authentication & Role Simulation Fixtures
# =====================================================================
@pytest.fixture(scope="session")
def auth_token():
    """
    Exchange test user credentials for a live Supabase JWT access token.
    Cached at session scope to minimize auth-service round-trips.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    test_user_email = os.getenv("TEST_USER_EMAIL")
    test_user_password = os.getenv("TEST_USER_PASSWORD")

    if not test_user_email or not test_user_password:
        raise ValueError("TEST_USER_EMAIL and TEST_USER_PASSWORD must be set in test.env.")

    url = f"{supabase_url}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": supabase_anon_key,
        "Content-Type": "application/json",
    }
    payload = {
        "email": test_user_email,
        "password": test_user_password,
    }

    response = requests.post(url, json=payload, headers=headers)
    assert response.status_code == 200, f"Failed to authenticate test user: {response.text}"

    return response.json().get("access_token")


@pytest.fixture(scope="session")
def authenticated_api_session(api_session, auth_token):
    """
    Extends base api_session by swapping the anonymous Bearer token 
    with the dynamic user JWT for RLS-protected resource validation.
    """
    api_session.headers["Authorization"] = f"Bearer {auth_token}"
    return api_session


@pytest.fixture
def anonymous_api_session(api_session):
    """
    Function-scoped fresh session configured strictly with anon-key level access 
    (stripping user-specific bearer state) to test unauthenticated edge rejections.
    """
    anon_session = requests.Session()
    anon_session.headers.update(
        {
            "apikey": os.getenv("SUPABASE_ANON_KEY"),
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
    )
    return anon_session


@pytest.fixture
def restricted_api_session():
    """
    Simulates a low-privilege or secondary user context for cross-user RLS isolation checks.
    Falls back gracefully to anon key if RESTRICTED_USER_JWT is unconfigured.
    """
    session = requests.Session()
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    restricted_token = os.getenv("RESTRICTED_USER_JWT") or supabase_anon_key  

    session.headers.update(
        {
            "apikey": supabase_anon_key,
            "Authorization": f"Bearer {restricted_token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
    )
    return session