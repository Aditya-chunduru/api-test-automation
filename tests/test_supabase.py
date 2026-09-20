"""
Pytest Collection Smoke Suite for Table Data Retrieval
- Validates basic endpoint availability and root list serialization contracts.
"""

# =====================================================================
# Module Imports & Purpose Ledger
# =====================================================================
import pytest  # Test framework foundation (retained for suite consistency & execution hooks)

# =====================================================================
# Table Data Read Tests
# =====================================================================
def test_get_table_data(api_session, base_url):
    """
    Baseline Read Check: Verify that querying the target table endpoint 
    returns HTTP 200 OK and serializes payload as a JSON array / list.
    """
    response = api_session.get(f"{base_url}/cart_items")

    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}: {response.text}"
    assert isinstance(response.json(), list), f"Expected response to be a list of records"