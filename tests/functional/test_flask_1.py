import pixelserver
from pixelserver import create_app

# redirect to /login
def test_index_1():
    app = create_app()
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 302
        
        
def test_login_1():
    app = create_app()
    with app.test_client() as test_client:
        response = test_client.get('/login')
        assert response.status_code == 200