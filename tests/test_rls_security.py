"""
Pytest RLS & Authorization Security Suite
- Validates read/write permissions for dynamically authenticated user context.
- Verifies Row-Level Security (RLS) enforcement against anonymous access.
- Ensures non-owned / cross-tenant record mutations trigger policy rejection.
"""

# =====================================================================
# Module Imports & Purpose Ledger
# =====================================================================
import pytest  # Test framework core (included for fixture dependency & suite uniformity)

# =====================================================================
# Authenticated User Operations
# =====================================================================
def test_authorized_endpoint(base_url, authenticated_api_session):
    """
    Contract & Auth Check: Verify dynamically authenticated JWT session 
    can query protected collection endpoints (200 OK + JSON list shape).
    """
    response = authenticated_api_session.get(f"{base_url}/products")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    assert isinstance(response.json(), list)


def test_user_can_insert_record(base_url, authenticated_api_session):
    """
    Write-Permit Check: Verify authenticated session can insert records 
    under valid RLS policy write rules (200/201 expected with representation preference).
    """
    payload = {
        "name": "Test Product 3"  # Target table schema attribute fixture
    }
    response = authenticated_api_session.post(f"{base_url}/products", json=payload)
    assert response.status_code in [200, 201], f"Insert failed: {response.text}"


# =====================================================================
# Anonymous & Cross-User RLS Boundary Enforcement
# =====================================================================
def test_unauthorized_user_cannot_access_protected_data(base_url, anonymous_api_session):
    """
    RLS Null-Isolation Check: Verify anonymous session querying an RLS-locked 
    table returns 200 OK with an empty array `[]` rather than leaking restricted rows.
    """
    response = anonymous_api_session.get(f"{base_url}/orders")
    assert response.status_code == 200 
    assert response.json() == [], f"Security leak: Unauthorized user received data: {response.text}"


def test_unauthorized_user_cannot_modify_unauthorized_record(base_url, restricted_api_session):
    """
    Mutation Guard Check: Verify restricted/secondary user session attempting 
    to PATCH a foreign or unowned primary key triggers strict policy denial (401/403/404).
    """
    foreign_id = "999999-restricted-record"
    payload = { "name": "Hacked Product" }

    response = restricted_api_session.patch(f"{base_url}/products/{foreign_id}", json=payload)
    assert response.status_code in [401, 403, 404], f"RLS Failure: Unauthorized mutation allowed ({response.status_code})"
    

