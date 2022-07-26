import pixelserver
from pixelserver import create_app

default_config_filename = "defaults.cfg" 
custom_config_filename = "pixelserver.cfg"
custom_light_config_filename = "customlight.cfg"
auth_config_filename = "auth.cfg"
auth_users_filename = "users.cfg"
log_filename = "/var/log/pixelserver.log"

# redirect to /login
def test_index_1():
    app = create_app(auth_config_filename, auth_users_filename, log_filename)
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 302
        
        
def test_login_1():
    app = create_app(auth_config_filename, auth_users_filename, log_filename)
    with app.test_client() as test_client:
        response = test_client.get('/login')
        assert response.status_code == 200