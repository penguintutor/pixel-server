from flask import Flask
import pixelserver
from pixelserver import create_app

# Note that this is not able to test csrf protection
# That is tested separately outside of 


# default configs use alternative as required for each test
default_config_filename = "tests/configs/defaults.cfg" 
custom_config_filename = "tests/configs/pixelserver.cfg"
custom_light_config_filename = "tests/configs/customlight.cfg"
auth_config_filename = "tests/configs/auth.cfg"
auth_users_filename = "tests/configs/users.cfg"
log_filename = "tests/log/pixelserver.log"

# special configs
# No network_allow_always (no guest)
auth_config_noguest = "tests/configs/auth-noguest.cfg"

# Authorized on network return index.html
def test_index_1():
    app = create_app(auth_config_filename, auth_users_filename, log_filename)
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert "guest" in str(response.data)

# redirect to /login
def test_index_2():
    app = create_app(auth_config_noguest, auth_users_filename, log_filename)
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 302
        assert response.location == "http://localhost/login"

# Network not authorised to return /login
def test_login_page_2():
    app = create_app(auth_config_filename, auth_users_filename, log_filename)
    with app.test_client() as test_client:
        response = test_client.get('/login')
        assert response.status_code == 200
        assert 'Please login to access' in str(response.data)
       
def test_login_success_1():
    app = create_app(auth_config_filename, auth_users_filename, log_filename, csrf_enable=False)
    with app.app_context():
        test_client = app.test_client() 
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">admin</button>' in str(response.data)

def test_login_fail_1():
    app = create_app(auth_config_filename, auth_users_filename, log_filename, csrf_enable=False)
    with app.app_context():
        test_client = app.test_client() 
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Invalid login attempt' in str(response.data)
        
# invalid characters in username
def test_login_fail_2():
    app = create_app(auth_config_filename, auth_users_filename, log_filename, csrf_enable=False)
    with app.app_context():
        test_client = app.test_client() 
        response = test_client.post("/login", data={
                "username": "adm<d>in",
                "password": "pixel",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Invalid login attempt' in str(response.data)