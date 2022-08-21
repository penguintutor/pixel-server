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
    'default' : "defaults.cfg",
    'custom' : "pixelserver.cfg",
    'sha256' : "sha256.cfg",
    'light' : "customlight.cfg",
    'auth' : "auth.cfg",
    'users' : "users.cfg"
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
    

# Creates users using json config file
def test_create_users_1():
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
                    "username": this_user['username']
                }, follow_redirects=True)
            # if expect fail username
            if this_user["error"] == "username":
                assert response.status_code == 200
                assert this_user["errormsg"] in str(response.data)
                continue
            else:
                assert response.status_code == 200
                assert '<input type="text" id="username" name="username" value="'+this_user['username']+'" readonly>' in str(response.data)
            # Add a password
            response = test_client.post("/newuser", data={
                    "newuser" : "userpassword",
                    "username" : this_user['username'],
                    "password": this_user['password'],
                    "password2": this_user['password'],
                }, follow_redirects=True)
            if this_user["error"] == "password":
                assert response.status_code == 200
                assert this_user["errormsg"] in str(response.data)
                continue
            else:
                assert response.status_code == 200
                expect_string = '<input type="text" id="username" name="username" value="'+this_user['username']+'">' 
                assert expect_string in str(response.data)


# Edit users
def test_edit_users_1():
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
            # skip any with errors that prevent them being created
            if this_user['error'] == "username" or this_user['error'] == "password":
                continue
            # Edit and change values from newuser calls edituser
            data_dict = {
                    "edituser" : "edituser",
                    "currentusername" : this_user['username'],
                    "username" : this_user['username'],
                    "realname" : this_user['realname'],
                    "email": this_user['email'],
                    "description": this_user['description']
                }
            if (this_user['admin'] == "True"):
                data_dict['admin'] = "checked"
            response = test_client.post("/edituser", data=data_dict, follow_redirects=True)
            if this_user['error'] == "edit":
                assert response.status_code == 200
                assert this_user['errormsg'] in str(response.data)
                continue
            assert response.status_code == 200
            # Check returns to user table - but not check updates at this point
            assert '<table id="users">' in str(response.data)
            # Load the edituser and check values set 
            response = test_client.get('/edituser', query_string={
                    "user" : this_user['username'],
                    "action" : "edit"
                })
            assert response.status_code == 200
            # check values
            eval_string = '<input type="text" id="realname" name="realname" value="{}">'.format(this_user['realname'])
            assert eval_string in str(response.data)
            if (this_user['admin'] == "True"):
                assert '<input type="checkbox" name="admin" checked="checked">' in str(response.data)
            else:
                assert '<input type="checkbox" name="admin">' in str(response.data)
            eval_string =  '<input type="text" id="email" name="email" value="{}">'.format(this_user['email'])
            assert eval_string in str(response.data)
            eval_string = '<input type="text" id="description" name="description" value="{}">'.format(this_user['description'])
            assert eval_string in str(response.data)