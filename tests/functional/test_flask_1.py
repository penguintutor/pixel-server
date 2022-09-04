from flask import Flask
import pixelserver
from pixelserver import create_app
import logging

# Note that this is not able to test csrf protection
# use csrf_enable = False in create_app() for any posts

# For log debugging use debug=True in create_app()
#  then using logging.debug

# That is tested separately outside of this. See TESTS.md for more details

# default configs use alternative as required for each test
default_config_filename = "tests/configs/defaults_test.cfg"
custom_config_filename = "tests/configs/pixelserver_test.cfg"
custom_light_config_filename = "tests/configs/customlight_test.cfg"
auth_config_filename = "tests/configs/auth_test.cfg"
auth_users_filename = "tests/configs/users_test.cfg"

# default use _log_filename which uses directory factory
log_filename = "pixelserver.log"

# special configs
# No network_allow_always (no guest)
auth_config_noguest = "tests/configs/auth-noguest_test.cfg"
auth_config_none = "tests/configs/auth-allownone_test.cfg"
auth_config_proxy = "tests/configs/auth-proxy_test.cfg"

# file does not exist
auth_users_nofile = "tests/configs/users_notexist_test.cfg"


def tmp_dir_setup (tmp_path_factory):
    global _log_directory, _log_filename
    _log_directory = str(tmp_path_factory.mktemp("log"))
    _log_filename = _log_directory + "/" + log_filename

# Setup path factory and empty user file
def test_setup_factory(tmp_path_factory):
    tmp_dir_setup(tmp_path_factory)

# Authorized on network return index.html
def test_index_1():
    app = create_app(auth_config_filename, auth_users_filename, _log_filename, debug=True)
    logging.debug ("*TEST guest network")
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert "guest" in str(response.data)

# redirect to /login
def test_index_2():
    app = create_app(auth_config_noguest, auth_users_filename, _log_filename, debug=True)
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 302
        assert (response.location == "http://localhost/login") or (response.location == "/login")

# Not allowed
def test_index_3():
    app = create_app(auth_config_none, auth_users_filename, _log_filename, debug=True)
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 302
        assert (response.location == "http://localhost/invalid") or (response.location == "/invalid")

# Test proxy- authentication required
def test_index_4():
    app = create_app(auth_config_proxy, auth_users_filename, _log_filename, debug=True)
    logging.debug ("*TEST Test proxy - login required")
    with app.test_client() as test_client:
        response = test_client.get('/',
            headers={'X-Real_IP': '192.168.0.22'}
            )
        assert response.status_code == 302
        assert (response.location == "http://localhost/login") or (response.location == "/login")

# Test proxy - address not allowed
def test_index_5():
    app = create_app(auth_config_proxy, auth_users_filename, _log_filename, debug=True)
    logging.info ("*TEST Test proxy - invalid")
    with app.test_client() as test_client:
        response = test_client.get('/',
            headers={'X-Real_IP': '10.5.5.1'}
            )
        assert response.status_code == 302
        assert response.location == "http://localhost/invalid"

# Test proxy - no login required
def test_index_5():
    app = create_app(auth_config_proxy, auth_users_filename, _log_filename, debug=True)
    logging.info ("*TEST Test proxy - guest login")
    with app.test_client() as test_client:
        response = test_client.get('/',
            headers={'X-Real_IP': '192.168.3.7'}
            )
        assert response.status_code == 200
        assert "guest" in str(response.data)

# Network not authorised to return /login
def test_login_page_2():
    app = create_app(auth_config_filename, auth_users_filename, _log_filename, debug=True)
    with app.test_client() as test_client:
        response = test_client.get('/login')
        assert response.status_code == 200
        assert 'Please login to access' in str(response.data)

def test_login_success_1():
    app = create_app(auth_config_filename, auth_users_filename, _log_filename, csrf_enable=False, debug=True)
    with app.app_context():
        test_client = app.test_client()
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">admin</button>' in str(response.data)

def test_login_fail_1():
    app = create_app(auth_config_filename, auth_users_filename, _log_filename, csrf_enable=False, debug=True)
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
    app = create_app(auth_config_filename, auth_users_filename, _log_filename, csrf_enable=False, debug=True)
    with app.app_context():
        test_client = app.test_client()
        response = test_client.post("/login", data={
                "username": "adm<d>in",
                "password": "pixel",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Invalid login attempt' in str(response.data)

def test_login_fail_3():
    app = create_app(auth_config_filename, auth_users_filename, _log_filename, csrf_enable=False, debug=True)
    with app.app_context():
        test_client = app.test_client()
        response = test_client.post("/login", data={
                "username": "admin:noallowed",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Invalid login attempt' in str(response.data)
        
        