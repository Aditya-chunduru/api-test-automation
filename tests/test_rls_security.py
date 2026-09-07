def test_authorized_endpoint(base_url, authenticated_api_session):
    """Verify that the dynamically authenticated user can access protected endpoints."""
    # Replace 'your_protected_table' with an actual table name in your Supabase database
    response = authenticated_api_session.get(f"{base_url}/products")
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    assert isinstance(response.json(), list)

def test_user_can_insert_record(base_url, authenticated_api_session):
    """Verify that the authenticated user can write data to their table."""
    payload = {
        "name": "Test Product 3"  # Replace with your actual table column and value
    }
    
    response = authenticated_api_session.post(f"{base_url}/products", json=payload)
    
    assert response.status_code in [200, 201], f"Insert failed: {response.text}"

def test_unauthorized_user_cannot_access_protected_data(base_url, anonymous_api_session):
    """Verify that unauthenticated or unauthorized roles are blocked by RLS/Auth policies."""
    response = anonymous_api_session.get(f"{base_url}/orders")

    assert response.status_code == 200 
    assert response.json() == [], f"Security leak: Unauthorized user received data: {response.text}"

def test_unauthorized_user_cannot_modify_unauthorized_record(base_url, restricted_api_session):
    """Verify that a user cannot update records they do not own."""
    foreign_id = "999999-restricted-record"
    payload = { "name": "Hacked Product" }

    response = restricted_api_session.patch(f"{base_url}/products/{foreign_id}", json=payload)

    assert response.status_code in [401, 403, 404], f"RLS Failure: Unauthorized mutation allowed ({response.status_code})"
    

