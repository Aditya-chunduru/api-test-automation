import os
from pathlib import Path
import pytest
import requests
from dotenv import load_dotenv  # type: ignore

# Locate project root and test.env explicitly
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / "test.env"  # Use BASE_DIR / "test.env" if test.env is inside /tests

# Debug check: verify if the file exists and load it with override
if not ENV_PATH.exists():
    # Fallback to same directory if root check fails
    ENV_PATH = BASE_DIR / "test.env"

if not os.getenv("SUPABASE_URL") and ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    load_dotenv(override=True)  # Ensure we load even if some vars exist


@pytest.fixture(scope="session")
def base_url():
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        raise ValueError(
            f"Failed to load SUPABASE_URL. Checked path: {ENV_PATH.resolve()}"
        )
    return f"{supabase_url}/rest/v1"


@pytest.fixture(scope="session")
def api_session():
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

@pytest.fixture(scope="session")
def auth_token():
    """Automatically logs in the test user to fetch a fresh JWT before tests run."""
    supabase_url =os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
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
        "password": test_user_password
    }

    response = requests.post(url, json=payload, headers=headers)
    assert response.status_code == 200, f"Failed to authenticate test user: {response.text}"

    return response.json().get("access_token")


@pytest.fixture(scope="session")
def authenticated_api_session(api_session, auth_token):
    """Extends your existing session to swap in the dynamic user JWT for protected tests."""
    api_session.headers["Authorization"] = f"Bearer {auth_token}"
    return api_session


@pytest.fixture
def anonymous_api_session(api_session):
    """Session with zero credentials or stripped authorization headers (Supabase anon key only)."""
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
    """Session mapped to a low-privilege or secondary test user for isolation checks."""
    session = requests.Session()
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    restricted_token = os.getenv("RESTRICTED_USER_JWT")

    session.headers.update(
        {
            "apikey": supabase_anon_key,
            "Authorization": f"Bearer {restricted_token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
    )
    return session
