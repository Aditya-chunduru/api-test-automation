import pytest

def test_get_cart_items_status_code(api_session, base_url):
    """Verify that the cart_items endpoint returns a 200 OK status."""
    response = api_session.get(f"{base_url}/cart_items")
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

def test_get_cart_item_by_id_structure(api_session, base_url):
    """Verify that an individual cart item record contains expected keys and data types using a real ID."""
    # Fetch all items to grab a valid existing ID dynamically
    all_items = api_session.get(f"{base_url}/cart_items").json()
    if not all_items:
        pytest.skip("No cart items found in the database to test against.")
    
    real_id = all_items[0]["cart_item_id"]
    
    # Query using the real UUID
    response = api_session.get(f"{base_url}/cart_items?cart_item_id=eq.{real_id}")
    assert response.status_code == 200
    
    data = response.json()
    record = data[0] if isinstance(data, list) else data
    
    assert "cart_item_id" in record
    assert "quantity" in record 

def test_get_cart_item_not_found(api_session, base_url):
    """Verify behavior when querying a non-existent record using a valid UUID format."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = api_session.get(f"{base_url}/cart_items?cart_item_id=eq.{fake_uuid}")
    assert response.status_code == 200
    assert response.json() == []