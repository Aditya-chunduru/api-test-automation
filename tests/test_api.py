"""
Pytest Contract & Smoke Suite for /cart_items Endpoints
- Validates basic collection availability (200 OK).
- Verifies PostgREST single-record UUID projection schema contract.
- Validates PostgREST empty-result convention (200 OK with empty array [] for missing IDs).
"""

# =====================================================================
# Module Imports & Purpose Ledger
# =====================================================================
import pytest  # Test runner framework, fixture dependency injection, and flow control (skip)

# =====================================================================
# Test Cases
# =====================================================================
def test_get_cart_items_status_code(api_session, base_url):
    """
    Smoke check: Verify that root collection query returns HTTP 200 OK.
    """
    response = api_session.get(f"{base_url}/cart_items")
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"


def test_get_cart_item_by_id_structure(api_session, base_url):
    """
    Contract check: Verify single-record shape using a dynamically extracted live UUID.
    Safely skips if table is unseeded/empty.
    """
    # Fetch collection baseline to source a valid existing primary key
    all_items = api_session.get(f"{base_url}/cart_items").json()
    if not all_items:
        pytest.skip("No cart items found in the database to test against.")
    
    real_id = all_items[0]["cart_item_id"]
    
    # Query specific record via PostgREST equality filter
    response = api_session.get(f"{base_url}/cart_items?cart_item_id=eq.{real_id}")
    assert response.status_code == 200
    
    data = response.json()
    record = data[0] if isinstance(data, list) else data
    
    # Assert core field existence contract
    assert "cart_item_id" in record
    assert "quantity" in record 


def test_get_cart_item_not_found(api_session, base_url):
    """
    PostgREST Behavior Check: Verify that querying a syntactically valid UUID 
    with zero database matches returns 200 OK and an empty list `[]`, matching 
    PostgREST spec-compliant behavior.
    """
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = api_session.get(f"{base_url}/cart_items?cart_item_id=eq.{fake_uuid}")
    assert response.status_code == 200
    assert response.json() == []