from flask import Flask
import pixelserver
from pixelserver import create_app
from pixelserver.pixels import Pixels
import logging
import shutil
import json
import string
import random

# Note that this is not able to test csrf protection
# use csrf_enable = False in create_app() for any posts

# For log debugging use debug=True in create_app()
#  then using logging.debug 

# Users tmp_path_factory - files will be copied to:
#/tmp/pytest-of-<username>/pytest-current/log?/pixelserver.log

## Automated tests - generates different passwords to test user password
# uses lowercase, uppercase, digits and special characters
allowed_chars = list(string.ascii_letters + string.digits + string.punctuation + " ")

# how many times to change the password
num_changes = 20

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


# performs num_changes x password changes and checks each is successful
def test_password_changer_1():
    username = "stduser1"
    current_password = "pixel1login2"
    first_password = current_password # use to reset password at the end
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST automated password changer")
    with app.test_client() as test_client:
        # Login
        response = test_client.get('/login')
        assert response.status_code == 200
        assert "Please login to access" in str(response.data)
        for i in range (num_changes):
            # Choose new password
            new_password = _create_valid_password()
            # Perform login using current_password
            response = test_client.post("/login", data={
                    "username": username,
                    "password": current_password,
                }, follow_redirects=True)
            assert response.status_code == 200
            eval_string = '<button type="button" id="profilebutton" onclick="profile()">{}</button>'.format(username)
            assert eval_string in str(response.data)
            # Go to profile page
            response = test_client.get('/profile')
            assert response.status_code == 200
            assert "The following items are readonly. Please contact an admin for any changes." in str(response.data)
            # Go to change password page
            response = test_client.get('/password')
            assert response.status_code == 200
            assert '<input type="hidden" name="passwordchange" value="passwordchange">' in str(response.data)
            # Change to new password
            response = test_client.post("/password", data={
                    "passwordchange": "passwordchange",
                    "currentpassword": current_password,
                    "newpassword": new_password,
                    "repeatpassword": new_password,
                }, follow_redirects=True)
            assert response.status_code == 200
            assert 'Password changed' in str(response.data)
            # Swap to new password
            current_password = new_password
            # logout 
            response = test_client.get('/logout')
            assert response.status_code == 200
            assert "Logged out" in str(response.data)
            assert "Please login to access" in str(response.data)
        # outside loop - check final login
        response = test_client.post("/login", data={
                    "username": username,
                    "password": current_password,
                }, follow_redirects=True)
        assert response.status_code == 200
        eval_string = '<button type="button" id="profilebutton" onclick="profile()">{}</button>'.format(username)
        assert eval_string in str(response.data) 
        # Restore original password
        new_password = first_password
        response = test_client.post("/password", data={
                "passwordchange": "passwordchange",
                "currentpassword": current_password,
                "newpassword": new_password,
                "repeatpassword": new_password,
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Password changed' in str(response.data)
        # Swap to new password
        current_password = new_password
        # logout 
        response = test_client.get('/logout')
        assert response.status_code == 200
        assert "Logged out" in str(response.data)
        assert "Please login to access" in str(response.data)
        # Check restored first_password
        response = test_client.post("/login", data={
                    "username": username,
                    "password": first_password,
                }, follow_redirects=True)
        assert response.status_code == 200
        eval_string = '<button type="button" id="profilebutton" onclick="profile()">{}</button>'.format(username)
        assert eval_string in str(response.data) 


# Test with long passwords (10 x)
def test_password_change_long_1():
    username = "stduser1"
    current_password = "pixel1login2"
    first_password = current_password # use to reset password at the end
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST long passwords")
    with app.test_client() as test_client:
        # Login
        response = test_client.get('/login')
        assert response.status_code == 200
        assert "Please login to access" in str(response.data)
        for i in range (10):
            # Choose new password
            new_password = _create_valid_password(max_chars = 255)
            # Perform login using current_password
            response = test_client.post("/login", data={
                    "username": username,
                    "password": current_password,
                }, follow_redirects=True)
            assert response.status_code == 200
            eval_string = '<button type="button" id="profilebutton" onclick="profile()">{}</button>'.format(username)
            assert eval_string in str(response.data)
            # Go to profile page
            response = test_client.get('/profile')
            assert response.status_code == 200
            assert "The following items are readonly. Please contact an admin for any changes." in str(response.data)
            # Go to change password page
            response = test_client.get('/password')
            assert response.status_code == 200
            assert '<input type="hidden" name="passwordchange" value="passwordchange">' in str(response.data)
            # Change to new password
            response = test_client.post("/password", data={
                    "passwordchange": "passwordchange",
                    "currentpassword": current_password,
                    "newpassword": new_password,
                    "repeatpassword": new_password,
                }, follow_redirects=True)
            assert response.status_code == 200
            assert 'Password changed' in str(response.data)
            # Swap to new password
            current_password = new_password
            # logout 
            response = test_client.get('/logout')
            assert response.status_code == 200
            assert "Logged out" in str(response.data)
            assert "Please login to access" in str(response.data)
        # outside loop - check final login
        response = test_client.post("/login", data={
                    "username": username,
                    "password": current_password,
                }, follow_redirects=True)
        assert response.status_code == 200
        eval_string = '<button type="button" id="profilebutton" onclick="profile()">{}</button>'.format(username)
        assert eval_string in str(response.data) 
        # Restore original password
        new_password = first_password
        response = test_client.post("/password", data={
                "passwordchange": "passwordchange",
                "currentpassword": current_password,
                "newpassword": new_password,
                "repeatpassword": new_password,
            }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Password changed' in str(response.data)
        # Swap to new password
        current_password = new_password
        # logout 
        response = test_client.get('/logout')
        assert response.status_code == 200
        assert "Logged out" in str(response.data)
        assert "Please login to access" in str(response.data)
        # Check restored first_password
        response = test_client.post("/login", data={
                    "username": username,
                    "password": first_password,
                }, follow_redirects=True)
        assert response.status_code == 200
        eval_string = '<button type="button" id="profilebutton" onclick="profile()">{}</button>'.format(username)
        assert eval_string in str(response.data) 

# check with passwords that are too short
def test_short_passwords_1():
    username = "stduser1"
    current_password = "pixel1login2"
    new_passwords = ["", "1", "d", "$", "pas", "23d", "343", "34£45!", "?GHNK"]
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST short password changer")
    with app.test_client() as test_client:
        response = test_client.post("/login", data={
                "username": username,
                "password": current_password,
            }, follow_redirects=True)
        assert response.status_code == 200
        eval_string = '<button type="button" id="profilebutton" onclick="profile()">{}</button>'.format(username)
        assert eval_string in str(response.data)
        for test_password in new_passwords:
            response = test_client.post("/password", data={
                    "passwordchange": "passwordchange",
                    "currentpassword": current_password,
                    "newpassword": test_password,
                    "repeatpassword": test_password,
                }, follow_redirects=True)
            assert response.status_code == 200
            assert 'Password must be at least 8 characters long' in str(response.data)

# check with passwords without digits
def test_nodigit_passwords_1():
    username = "stduser1"
    current_password = "pixel1login2"
    new_passwords = ["smithjhek", "kjfkjkljkl", "ade%revfde", "!dkjklkrk$", "?GdddrHNK"]
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST nodigit password changer")
    with app.test_client() as test_client:
        response = test_client.post("/login", data={
                "username": username,
                "password": current_password,
            }, follow_redirects=True)
        assert response.status_code == 200
        eval_string = '<button type="button" id="profilebutton" onclick="profile()">{}</button>'.format(username)
        assert eval_string in str(response.data)
        for test_password in new_passwords:
            response = test_client.post("/password", data={
                    "passwordchange": "passwordchange",
                    "currentpassword": current_password,
                    "newpassword": test_password,
                    "repeatpassword": test_password,
                }, follow_redirects=True)
            assert response.status_code == 200
            assert 'Password must contain at least one letter and one digit' in str(response.data)

# check with passwords without letters
def test_noletter_passwords_1():
    username = "stduser1"
    current_password = "pixel1login2"
    new_passwords = ["13234323", "32332980£%", "323288898!", "38989987", "0000  000"]
    app = create_app(configs['auth'], configs['users'], _log_filename, csrf_enable=False, debug=True)
    pixels = Pixels(configs['default'], "", "", run=False)
    logging.debug ("*TEST nodigit password changer")
    with app.test_client() as test_client:
        response = test_client.post("/login", data={
                "username": username,
                "password": current_password,
            }, follow_redirects=True)
        assert response.status_code == 200
        eval_string = '<button type="button" id="profilebutton" onclick="profile()">{}</button>'.format(username)
        assert eval_string in str(response.data)
        for test_password in new_passwords:
            response = test_client.post("/password", data={
                    "passwordchange": "passwordchange",
                    "currentpassword": current_password,
                    "newpassword": test_password,
                    "repeatpassword": test_password,
                }, follow_redirects=True)
            assert response.status_code == 200
            assert 'Password must contain at least one letter and one digit' in str(response.data)


def _create_valid_password (max_chars = 20):
    # First create totally random string
    password = ''.join(random.choice(allowed_chars) for i in range(random.randint(8,max_chars)))
    # strip spaces from end 
    password = password.strip()
    # If no alpha add one to end
    if not _has_lowercase(password):
        password += random.choice(string.ascii_lowercase)
    if not _has_uppercase(password):
        password += random.choice(string.ascii_uppercase)
    if not _has_digit(password):
        password += random.choice(string.digits)
    # Now loop checking we have sufficient characters
    while (len(password) < 8):
        password += random.choice(string.printable)
    return password
    
    
            
def _has_digit (string):
    for i in list(string):
        if i.isdigit():
            return True
    return False

def _has_lowercase (string):
    for i in list(string):
        if i.islower():
            return True
    return False
    
def _has_uppercase (string):
    for i in list(string):
        if i.isupper():
            return True
    return False