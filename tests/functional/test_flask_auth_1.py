from flask import Flask
import pixelserver
from pixelserver import create_app
import logging

# Note that this is not able to test csrf protection
# use csrf_enable = False in create_app() for any posts

## Tests using different auth_config values

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
auth_config_nofile = "tests/configs/auth-config-notexist.cfg"     # File does not exist

# file does not exist
auth_users_nofile = "tests/configs/users_notexist_test.cfg"



def tmp_dir_setup (tmp_path_factory):
    global _log_directory, _log_filename
    _log_directory = str(tmp_path_factory.mktemp("log"))
    _log_filename = _log_directory + "/" + log_filename

# Setup path factory and empty user file
def test_setup_factory(tmp_path_factory):
    tmp_dir_setup(tmp_path_factory)

# If not auth config file then default to login required
# redirect to /login
def test_indexnoconfig_1():
    app = create_app(auth_config_nofile, auth_users_filename, _log_filename, debug=True)
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 302
        assert (response.location == "http://localhost/login") or (response.location == "/login")

# If no users file - or no users in users file then gives warning
# redirect to /login
def test_login_nousers_1():
    app = create_app(auth_config_nofile, auth_users_nofile, _log_filename, debug=True)
    with app.test_client() as test_client:
        # First check we get redirect to /login
        response = test_client.get('/')
        assert response.status_code == 302
        assert (response.location == "http://localhost/login") or (response.location == "/login")
        # Now get login page and check it gives warning message
        response = test_client.get('/login')
        assert response.status_code == 200
        assert "No users defined or missing users file. Run createadmin.py through the shell to setup an admin user." in str(response.data)
        
# checks don't get the warning that no users file if we have a users file
# redirect to /login
def test_loginpage_users_1():
    app = create_app(auth_config_nofile, auth_users_filename, _log_filename, debug=True)
    with app.test_client() as test_client:
        # First check we get redirect to /login
        response = test_client.get('/')
        assert response.status_code == 302
        assert (response.location == "http://localhost/login") or (response.location == "/login")
        # Now get login page and check it gives warning message
        response = test_client.get('/login')
        assert response.status_code == 200
        assert not("No users defined or missing users file." in str(response.data))