import sys
sys.path.append("/app")

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Families" in response.data  # checks if the page contains the title
    assert b"Add Family" in response.data  # checks for a key button/link
    
def test_add_family_route(client):
    response = client.get('/add-family')  # adjust if needed
    assert response.status_code == 200

def test_create_family(client):
    response = client.post('/add-family', data={'name': 'Test Family'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Test Family' in response.data
    # Further checks can be added to verify database state if needed