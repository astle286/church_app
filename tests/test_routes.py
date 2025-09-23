def test_families_page(client):
    response = client.get('/families')  # adjust if your route is different
    assert response.status_code == 200
    assert b"Families" in response.data  # checks if the page contains the title
