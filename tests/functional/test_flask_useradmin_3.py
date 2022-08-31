from flask import Flask
import pixelserver
from pixelserver import create_app
from pixelserver.pixels import Pixels
import logging
import shutil
import json

# Note that this is not able to test csrf protection
# use csrf_enable = False in create_app() for any posts

# For log debugging use debug=True in create_app()
#  then using logging.debug

# Users tmp_path_factory - files will be copied to:
#/tmp/pytest-of-<username>/pytest-current/log?/pixelserver.log

## Tests using supplied data from usertests.json
# Allows tests of different user data which should or should not be valid
# For each test set all data, error is the action it should fail on
# errormsg should be what message is received

_config_src_directory = "tests/configs/"

# default use _log_filename which uses directory factory
log_filename = "pixelserver.log"

# JSON file with data to test with
data_file ="tests/data/usertests.json"

# name of config files - will be mapped to temp directory
# In tests use configs{} instead.
config_filenames = {
    'default' : "defaults_test.cfg",
    'custom' : "pixelserver_test.cfg",
    'sha256' : "sha256_test.cfg",
    'light' : "customlight_test.cfg",
    'auth' : "auth_test.cfg",
    'users' : "users_test.cfg"
}


# default config files - created using tmp_dir_setup
configs = {}

def tmp_dir_setup (tmp_path_factory):
    global _log_directory, _log_filename, _config_directory
    _log_directory = str(tmp_path_factory.mktemp("log"))
    _log_filename = _log_directory + "/" + log_filename
    _config_directory = str(tmp_path_factory.mktemp("config"))
    # for all filenames copy files into tempdirectory and update configs
    for key, value in config_filenames.items():
        configs[key] = _config_directory + "/" + value
        # copy existing file to new location
        shutil.copyfile(_config_src_directory + value, configs[key])


# Setup path factory and empty user file
def test_setup_factory(tmp_path_factory):
    global user_data
    tmp_dir_setup(tmp_path_factory)
    # load json file
    f = open (data_file)
    user_data = json.load(f)
    f.close()


# Creates users using json config file - OOS = Out-of-sequence tests
def test_create_user_oos_1():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST add new user")
    with app.test_client() as test_client:
        # Even though guest straight to login page
        response = test_client.get('/login')
        assert response.status_code == 200
        assert "Please login to access" in str(response.data)
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">admin</button>' in str(response.data)
        # loop over all new users
        for this_user in user_data:
            # Add new user stage 1 (no data empty form)
            response = test_client.post("/newuser", follow_redirects=True)
            assert response.status_code == 200
            assert '<input type="hidden" name="newuser" value="newuser">' in str(response.data)
            # stage 2 add "newuser1"
            response = test_client.post("/newuser", data={
                    "newuser" : "newuser",
                    "username": "alloweduser"
                }, follow_redirects=True)
            # pass this stage
            assert response.status_code == 200
            assert '<input type="text" id="username" name="username" value="alloweduser" readonly>' in str(response.data)
            # Trying to add a new user with a username that already exists - so expect fail
            # Add a password
            response = test_client.post("/newuser", data={
                    "newuser" : "userpassword",
                    "username" : "stduser1",
                    "password": this_user['password'],
                    "password2": this_user['password'],
                }, follow_redirects=True)
            # should give a 200 succes - but then error message
            assert response.status_code == 200
            expect_string = 'User already exists'
            assert expect_string in str(response.data)


