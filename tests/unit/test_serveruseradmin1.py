from pixelserver.serveruseradmin import ServerUserAdmin

_test_user_file = "user.cfg" 
_user_filename = None

def tmp_dir_setup (tmp_path_factory):
    global _user_filename
    _user_filename = str(tmp_path_factory.mktemp("users") / "user.cfg")


# Test creating a new user
def test_add_user1(tmp_path_factory):
    tmp_dir_setup(tmp_path_factory)
    user_admin = ServerUserAdmin(_user_filename)
    result = user_admin.add_user(
        "test1", "password", 
        "Test User 1",
        "admin", "me@here.com",
        "")
    assert result == "success"
    assert user_admin.user_exists("test1")
    
def test_add_another_user():
    user_admin = ServerUserAdmin(_user_filename)
    result = user_admin.add_user(
        "longerusername", "password123", 
        "Person Real Name",
        "normal", "",
        "")
    assert result == "success"
    assert user_admin.user_exists("longerusername")
    
# password includes :
def test_add_user_2():
    user_admin = ServerUserAdmin(_user_filename)
    user_admin.add_user(
        "test2", "password123!:4", 
        "",
        "normal", "email@somewhere.com",
        "User has no real name")
    assert user_admin.user_exists("longerusername")
    
# Check if users added previously still exists
def test_persistant_users():
    user_admin = ServerUserAdmin(_user_filename)
    assert user_admin.user_exists("test1")  
    assert user_admin.user_exists("longerusername")
    
# Check user doesn't exist
def test_invalid_user():
    user_admin = ServerUserAdmin(_user_filename)
    assert not user_admin.user_exists("invalid1")    
    
    
# Test passwords
def test_user_password():
    user_admin = ServerUserAdmin(_user_filename)
    assert user_admin.check_username_password ("longerusername",
        "password123")
    
    
def test_incorrect_password():
    user_admin = ServerUserAdmin(_user_filename)
    assert not user_admin.check_username_password ("longerusername",
        "passw0rd123")
    
    
# Test permissions
def test_user1_admin():
    user_admin = ServerUserAdmin(_user_filename)
    assert user_admin.check_admin ("test1")
    
def test_user2_not_admin():
    user_admin = ServerUserAdmin(_user_filename)
    assert not user_admin.check_admin ("test2")
    
    
# Test handling of invalid username (includes a :)
def test_username_colon():
    user_admin = ServerUserAdmin(_user_filename)
    result = user_admin.add_user(
        "user:name", "djkD38dhJ!", 
        "Username with colon",
        "normal", "email@test.com",
        "This should fail")
    assert result != "success"
    assert not user_admin.user_exists("user:name")

# Test allows password with : (as converted to hash)
def test_password_colon():
    user_admin = ServerUserAdmin(_user_filename)
    result = user_admin.add_user(
        "user_pass_colon", "djdd:8dhJ!", 
        "Password with colon",
        "normal", "email@test.com",
        "This should pass as colon allowed in password")
    assert result == "success"


# Test duplicate is rejected
def test_duplicate_user():
    user_admin = ServerUserAdmin(_user_filename)
    result = user_admin.add_user(
        "test1", "djddhJ!", 
        "Duplicate user",
        "normal", "email@test.com",
        "This should not be a success")
    assert result == "duplicate"


# Test successful change of username
def test_username_change():
    user_admin = ServerUserAdmin(_user_filename)
    result = user_admin.add_user(
        "oldusername", "pa'#swo!d123", 
        "My name",
        "normal", "",
        "")
    assert result == "success"
    assert user_admin.user_exists("oldusername")
    # change username here
    result = user_admin.update_user("oldusername", {"username":"newusername"})
    assert result == True
    assert not user_admin.user_exists("oldusername")
    assert user_admin.user_exists("newusername")
    # Also check full name to make sure it's the original entry
    assert user_admin.get_real_name("newusername") == "My name"
    
    

# Test changing username after creation - doesn't allow colon
def test_username_change_colon():
    user_admin = ServerUserAdmin(_user_filename)
    result = user_admin.add_user(
        "olduser01", ":a'#s:o!d123", 
        "My name",
        "normal", "",
        "")
    assert result == "success"
    assert user_admin.user_exists("olduser01")
    # change username here
    result = user_admin.update_user("oldusername", {"username":"new:username"})
    assert result == False
    assert user_admin.user_exists("olduser01")
    assert not user_admin.user_exists("new:username")
    # Also check full name to make sure it's the original entry
    assert user_admin.get_real_name("olduser01") == "My name"