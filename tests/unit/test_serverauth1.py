from pixelserver.serverauth import ServerAuth
import string
import random
import shutil

# Tests ServerAuth class

_config_src_directory = "tests/configs/"

_test_user_filename = "users_test.cfg" 
_test_auth_filename = "auth_test.cfg"

_user_filename = None
_auth_filename = None

def tmp_dir_setup (tmp_path_factory):
    global _user_filename, _auth_filename
    _test_path = str(tmp_path_factory.mktemp("users"))
    _user_filename = _test_path + "/" + _test_user_filename
    _auth_filename = _test_path + "/" + _test_auth_filename
    # copy existing config files
    shutil.copyfile(_config_src_directory + _test_user_filename, _user_filename)
    shutil.copyfile(_config_src_directory + _test_auth_filename, _auth_filename)

# Setup path factory and empty user file
def test_setup_factory(tmp_path_factory):
    tmp_dir_setup(tmp_path_factory)
    
def test_login_user_1():
    server_auth = ServerAuth(_auth_filename, _user_filename)
    result = server_auth.login_user ("admin", "pixel1login2", "192.168.2.2")
    assert result == True

def test_login_user_2():
    server_auth = ServerAuth(_auth_filename, _user_filename)
    result = server_auth.login_user ("stduser1", "pixel1login2", "192.168.2.2")
    assert result == True
    
def test_login_user_3():
    server_auth = ServerAuth(_auth_filename, _user_filename)
    result = server_auth.login_user ("adminuser1", "pixel1login2", "192.168.2.2")
    assert result == True

def test_login_user_4():
    server_auth = ServerAuth(_auth_filename, _user_filename)
    result = server_auth.login_user ("stduser2", "pixel1login2", "192.168.2.2")
    assert result == True

def test_login_user_fail_1():
    server_auth = ServerAuth(_auth_filename, _user_filename)
    result = server_auth.login_user ("admin", "pixel1login3", "192.168.2.2")
    assert result == False

def test_login_user_fail_2():
    server_auth = ServerAuth(_auth_filename, _user_filename)
    result = server_auth.login_user ("admintest", "pixel1login3", "192.168.2.2")
    assert result == False
    
def test_login_user_fail_3():
    server_auth = ServerAuth(_auth_filename, _user_filename)
    result = server_auth.login_user ("stduser1", "pixel1login2 ", "192.168.2.2")
    assert result == False

def test_login_user_fail_4():
    server_auth = ServerAuth(_auth_filename, _user_filename)
    result = server_auth.login_user ("stduser2", "Pixel1login2", "192.168.2.2")
    assert result == False

def test_login_user_fail_5():
    server_auth = ServerAuth(_auth_filename, _user_filename)
    result = server_auth.login_user ("stduser2", "pixel1login2:test", "192.168.2.2")
    assert result == False
    
# Make sure still works for login if no auth.cfg config file
def test_noauthcfg_user_1():
    server_auth = ServerAuth("no_auth_file.cfg", _user_filename)
    result = server_auth.login_user ("admin", "pixel1login2", "192.168.2.2")
    assert result == True