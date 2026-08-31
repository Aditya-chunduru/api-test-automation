def test_get_table_data(api_session, base_url):

    response = api_session.get(f"{base_url}/cart_items")

    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}: {response.text}"
    assert isinstance(response.json(), list), f"Expected response to be a list of records"
