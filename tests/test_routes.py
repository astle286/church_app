import sys
sys.path.append("/app")

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Families" in response.data  # checks if the page contains the title
    assert b"Add Family" in response.data  # checks for a key button/link
    