from serveruseradmin import ServerUserAdmin

_test_user_file = "user.cfg" 
_user_filename = None

def tmp_dir_setup (tmp_path_factory):
    global _user_filename
    _user_filename = str(tmp_path_factory.mktemp("users") / "user.cfg")


# Test creating a new user
def test_add_user1(tmp_path_factory):
    tmp_dir_setup(tmp_path_factory)
    user_admin = ServerUserAdmin(_user_filename)
    user_admin.add_user(
        "test1", "password", 
        "Test User 1",
        "admin", "me@here.com",
        "")
    assert user_admin.user_exists("test1")
    
def test_add_another_user():
    user_admin = ServerUserAdmin(_user_filename)
    user_admin.add_user(
        "longerusername", "password123", 
        "Person Real Name",
        "normal", "",
        "")
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
    
    
def test_user_password():
    user_admin = ServerUserAdmin(_user_filename)
    assert user_admin.check_username_password ("longerusername", "password123")
    
    
def test_incorrect_password():
    user_admin = ServerUserAdmin(_user_filename)
    assert not user_admin.check_username_password ("longerusername", "passw0rd123")