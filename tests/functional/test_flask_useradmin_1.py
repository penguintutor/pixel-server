from flask import Flask
import pixelserver
from pixelserver import create_app
from pixelserver.pixels import Pixels
import logging
import shutil

# Note that this is not able to test csrf protection
# use csrf_enable = False in create_app() for any posts

# For log debugging use debug=True in create_app()
#  then using logging.debug 

# Users tmp_path_factory - files will be copied to:
#/tmp/pytest-of-<username>/pytest-current/log?/pixelserver.log

_config_src_directory = "tests/configs/"

# default use _log_filename which uses directory factory
log_filename = "pixelserver.log"

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
    tmp_dir_setup(tmp_path_factory)

# Authorized on network return index.html
def test_admin_login_1():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    logging.debug ("*TEST login as admin")
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert "guest" in str(response.data)
        # Even though guest request login page
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


# Adds a new standard user newuser1
# Follows full route a normal user would do including
# login and navigating through settings
# Does not make any changes at the end
# Uses default settings
def test_add_user_1():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST add new user")
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert "guest" in str(response.data)
        # Even though guest request login page
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
        # Go to settings
        response = test_client.get('/settings')
        assert response.status_code == 200
        assert "Number LEDs:" in str(response.data)
        # Go to useradmin
        response = test_client.get('/useradmin')
        assert response.status_code == 200
        assert '<table id="users">' in str(response.data)
        # Add new user stage 1 (no data empty form)
        response = test_client.post("/newuser", follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="hidden" name="newuser" value="newuser">' in str(response.data)
        # stage 2 add "newuser1"
        response = test_client.post("/newuser", data={
                "newuser" : "newuser",
                "username": "newuser1"
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="text" id="username" name="username" value="newuser1" readonly>' in str(response.data)
        # Add a password
        response = test_client.post("/newuser", data={
                "newuser" : "userpassword",
                "username" : "newuser1",
                "password": "pixel1login2",
                "password2": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="text" id="username" name="username" value="newuser1">' in str(response.data)
        
# Adds a new admin user 
# Uses sha256
def test_add_user_2():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], configs['sha256'], "", run=False)
    logging.debug ("*TEST add admin user sha256")
    with app.test_client() as test_client:
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">admin</button>' in str(response.data)
        # Add new user stage 1 (no data empty form)
        response = test_client.post("/newuser", follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="hidden" name="newuser" value="newuser">' in str(response.data)
        # stage 2 add "adminuser"
        response = test_client.post("/newuser", data={
                "newuser" : "newuser",
                "username": "adminuser"
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="text" id="username" name="username" value="adminuser" readonly>' in str(response.data)
        # Add a password
        response = test_client.post("/newuser", data={
                "newuser" : "userpassword",
                "username" : "adminuser",
                "password": "pixel1login2",
                "password2": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="text" id="username" name="username" value="adminuser">' in str(response.data)
        # Edit and change values from newuser calls edituser
        response = test_client.post("/edituser", data={
                "edituser" : "edituser",
                "currentusername" : "adminuser",
                "username" : "adminuser",
                "realname" : "Admin user real name",
                "admin": "checked",
                "email": "user@example938.com",
                "description": "Admin user sha256"
            }, follow_redirects=True)
        assert response.status_code == 200
        # Check returns to user table - but not check admin is set at this point
        assert '<table id="users">' in str(response.data)
        # Load the edituser and check admin set 
        response = test_client.get('/edituser', query_string={
                "user" : "adminuser",
                "action" : "edit"
            })
        assert response.status_code == 200
        # check admin is set
        assert '<input type="checkbox" name="admin" checked="checked">' in str(response.data)
        
        
# Adds a new standard user 
# Uses sha256
def test_add_user_3():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], configs['sha256'], "", run=False)
    logging.debug ("*TEST add standard sha256 user")
    with app.test_client() as test_client:
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">admin</button>' in str(response.data)
        # Add new user stage 1 (no data empty form)
        response = test_client.post("/newuser", follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="hidden" name="newuser" value="newuser">' in str(response.data)
        # stage 2 add "stduser"
        response = test_client.post("/newuser", data={
                "newuser" : "newuser",
                "username": "stduser"
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="text" id="username" name="username" value="stduser" readonly>' in str(response.data)
        # Add a password
        response = test_client.post("/newuser", data={
                "newuser" : "userpassword",
                "username" : "stduser",
                "password": "pixel1login2",
                "password2": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="text" id="username" name="username" value="stduser">' in str(response.data)
        # Edit and change values from newuser calls edituser
        response = test_client.post("/edituser", data={
                "edituser" : "edituser",
                "currentusername" : "stduser",
                "username" : "stduser",
                "realname" : "Standard user real name",
                "email": "user2@example938.com",
                "description": "Standard user sha256"
            }, follow_redirects=True)
        assert response.status_code == 200
        # Check returns to user table - but not check admin is set at this point
        assert '<table id="users">' in str(response.data)
        # Load the edituser and check admin set 
        response = test_client.get('/edituser', query_string={
                "user" : "stduser",
                "action" : "edit"
            })
        assert response.status_code == 200
        # check admin is set
        assert '<input type="checkbox" name="admin">' in str(response.data)
        
# Test above users works
def test_user_added_1():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST new user works")
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert "guest" in str(response.data)
        # Even though guest request login page
        response = test_client.get('/login')
        assert response.status_code == 200
        assert "Please login to access" in str(response.data)
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "newuser1",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">newuser1</button>' in str(response.data)
        # check not admin by looking for settings button
        assert '<button type="button" id="settingsbutton" onclick="settings()">Settings</button>' not in str(response.data)

# Test above users works
def test_user_added_2():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST new user works")
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert "guest" in str(response.data)
        # Even though guest request login page
        response = test_client.get('/login')
        assert response.status_code == 200
        assert "Please login to access" in str(response.data)
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "adminuser",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">adminuser</button>' in str(response.data)
        # check not admin by looking for settings button
        assert '<button type="button" id="settingsbutton" onclick="settings()">Settings</button>' in str(response.data)

# Test above users works
def test_user_added_3():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST new user works")
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert "guest" in str(response.data)
        # Even though guest request login page
        response = test_client.get('/login')
        assert response.status_code == 200
        assert "Please login to access" in str(response.data)
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "stduser",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">stduser</button>' in str(response.data)
        # check not admin by looking for settings button
        assert '<button type="button" id="settingsbutton" onclick="settings()">Settings</button>' not in str(response.data)


# Test invalid password failed login
# includes special characters
def test_invalid_password_1():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST new user works")
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert "guest" in str(response.data)
        # Even though guest request login page
        response = test_client.get('/login')
        assert response.status_code == 200
        assert "Please login to access" in str(response.data)
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "newuser1",
                "password": "p<ixel:o!gin2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Invalid login attempt' in str(response.data)

# Test invalid password failed login
# only 1 character missing
def test_invalid_password_2():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST new user works")
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert "guest" in str(response.data)
        # Even though guest request login page
        response = test_client.get('/login')
        assert response.status_code == 200
        assert "Please login to access" in str(response.data)
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "adminuser",
                "password": "pixel1login",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Invalid login attempt' in str(response.data)

# Test invalid password failed login
# only change case
def test_invalid_password_3():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST new user works")
    with app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert "guest" in str(response.data)
        # Even though guest request login page
        response = test_client.get('/login')
        assert response.status_code == 200
        assert "Please login to access" in str(response.data)
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "stduser",
                "password": "Pixel1login",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Invalid login attempt' in str(response.data)

# Adds a duplicate user (fail)
def test_add_user_duplicate_1():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], configs['sha256'], "", run=False)
    logging.debug ("*TEST add duplicate user")
    with app.test_client() as test_client:
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">admin</button>' in str(response.data)
        # Add new user stage 1 (no data empty form)
        response = test_client.post("/newuser", follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="hidden" name="newuser" value="newuser">' in str(response.data)
        # stage 2 add "adminuser"
        response = test_client.post("/newuser", data={
                "newuser" : "newuser",
                "username": "stduser1"
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'User already exists, please try another username' in str(response.data)


        
# Adds a user - too short(fail)
def test_add_user_tooshort_1():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], configs['sha256'], "", run=False)
    logging.debug ("*TEST add user too short")
    with app.test_client() as test_client:
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">admin</button>' in str(response.data)
        # Add new user stage 1 (no data empty form)
        response = test_client.post("/newuser", follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="hidden" name="newuser" value="newuser">' in str(response.data)
        # stage 2 add "adminuser"
        response = test_client.post("/newuser", data={
                "newuser" : "newuser",
                "username": "new"
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Username must be minimum of 6 characters' in str(response.data)

        
# Adds a user - special character(fail)
def test_add_user_invalidchar_1():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], configs['sha256'], "", run=False)
    logging.debug ("*TEST add user special character")
    with app.test_client() as test_client:
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">admin</button>' in str(response.data)
        # Add new user stage 1 (no data empty form)
        response = test_client.post("/newuser", follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="hidden" name="newuser" value="newuser">' in str(response.data)
        # stage 2 add "adminuser"
        response = test_client.post("/newuser", data={
                "newuser" : "newuser",
                "username": "new:user1"
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Username must be letters and digits only' in str(response.data)
        
# Adds a user - special character(fail)
def test_add_user_invalidchar_2():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], configs['sha256'], "", run=False)
    logging.debug ("*TEST add user special character")
    with app.test_client() as test_client:
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">admin</button>' in str(response.data)
        # Add new user stage 1 (no data empty form)
        response = test_client.post("/newuser", follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="hidden" name="newuser" value="newuser">' in str(response.data)
        # stage 2 add "adminuser"
        response = test_client.post("/newuser", data={
                "newuser" : "newuser",
                "username": "newuser$"
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Username must be letters and digits only' in str(response.data)
        
# Adds a user - special character(fail)
def test_add_user_invalidchar_3():
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], configs['sha256'], "", run=False)
    logging.debug ("*TEST add user special character")
    with app.test_client() as test_client:
        # Perform login using admin user
        response = test_client.post("/login", data={
                "username": "admin",
                "password": "pixel1login2",
            }, follow_redirects=True)
        assert response.status_code == 200
        assert '<button type="button" id="profilebutton" onclick="profile()">admin</button>' in str(response.data)
        # Add new user stage 1 (no data empty form)
        response = test_client.post("/newuser", follow_redirects=True)
        assert response.status_code == 200
        assert '<input type="hidden" name="newuser" value="newuser">' in str(response.data)
        # stage 2 add "adminuser"
        response = test_client.post("/newuser", data={
                "newuser" : "newuser",
                "username": "new\'\'user1"
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Username must be letters and digits only' in str(response.data)