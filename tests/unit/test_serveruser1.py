from pixelserver.serveruser import ServerUser
import string
import random

# Tests ServerUser class

## Includes automated password tests - generates different passwords to test user password
# uses lowercase, uppercase, digits and special characters
allowed_chars = list(string.ascii_letters + string.digits + string.punctuation + " ")
num_changes = 20


test_user_details = [
    "username1", "$argon2id$v=19$m=102400,t=2,p=8$0ZzMvxnNwvxePMp+y7hpfA$rCupS+lnWHUdEeIVkUHAGQ",
    "Real name for username1",
    "standard",
    "email@dummydomain3874.com",
    "Description of username 1"
    ]
test_user2_details = [
    "username2", "$5$1948a2047f5743c4a64bde92919d3eec$25670be86447039a5e126fc8acaac5e4ee4bd7805fcb493074ea9877be03088c",
    "Real name for username2",
    "admin",
    "email@dummydomain3874.co.uk",
    "Description of username 2"
    ]

# Test creating a new user
# Adds all parameters 
def test_create_user1():
    user1 = ServerUser(
        "username", 
        "$argon2id$v=19$m=102400,t=2,p=8$0ZzMvxnNwvxePMp+y7hpfA$rCupS+lnWHUdEeIVkUHAGQ",
        "real name",
        "standard",
        "email@here33982.com",
        "Description of new user"
        )
    # Test each of the values
    assert user1.username == "username"
    assert user1.password_hash == "$argon2id$v=19$m=102400,t=2,p=8$0ZzMvxnNwvxePMp+y7hpfA$rCupS+lnWHUdEeIVkUHAGQ"   
    assert user1.real_name == "real name"
    assert user1.user_type == "standard"
    assert user1.email == "email@here33982.com"
    assert user1.description == "Description of new user"
    assert user1.is_admin() == False


# Test creating a new user
# Minimum details - admin 
# SHA256 password
def test_create_user2():
    user1 = ServerUser(
        "user",         # username very short - not permitted by serveradmin, but is allowed if created manually (eg. createadmin.py)
        "$5$1948a2047f5743c4a64bde92919d3eec$25670be86447039a5e126fc8acaac5e4ee4bd7805fcb493074ea9877be03088c",
        "",
        "admin",
        "",
        ""
        )
    # Test each of the values
    assert user1.username == "user"
    assert user1.password_hash == "$5$1948a2047f5743c4a64bde92919d3eec$25670be86447039a5e126fc8acaac5e4ee4bd7805fcb493074ea9877be03088c"   
    assert user1.real_name == ""
    assert user1.user_type == "admin"
    assert user1.email == ""
    assert user1.description == ""
    assert user1.is_admin() == True
    
# Test using example user
def test_create_user_3():
    user1 = ServerUser(*test_user_details)
    assert user1.username == test_user_details[0]
    assert user1.password_hash == test_user_details[1]
    assert user1.real_name == test_user_details[2]
    assert user1.user_type == test_user_details[3]
    assert user1.email == test_user_details[4]
    assert user1.description == test_user_details[5]
    assert user1.is_admin() == False
    
# Create user then change to admin
# Test using example user
def test_set_admin_1():
    user1 = ServerUser(*test_user_details)
    assert user1.is_admin() == False
    user1.user_type = "admin"
    assert user1.username == test_user_details[0]
    assert user1.password_hash == test_user_details[1]
    assert user1.real_name == test_user_details[2]
    assert user1.user_type == "admin"
    assert user1.email == test_user_details[4]
    assert user1.description == test_user_details[5]
    assert user1.is_admin() == True
    
# Create user then change to standard user
# Test using example user
def test_set_admin_2():
    user1 = ServerUser(*test_user2_details)
    assert user1.is_admin() == True
    user1.user_type = "standard"
    assert user1.username == test_user2_details[0]
    assert user1.password_hash == test_user2_details[1]
    assert user1.real_name == test_user2_details[2]
    assert user1.user_type == "standard"
    assert user1.email == test_user2_details[4]
    assert user1.description == test_user2_details[5]
    assert user1.is_admin() == False
    
# Fail to change to an invalid user type
# should leave as non admin
def test_set_admin_3():
    user1 = ServerUser(*test_user_details)
    assert user1.is_admin() == False
    user1.user_type = "admin1"
    assert user1.username == test_user_details[0]
    assert user1.password_hash == test_user_details[1]
    assert user1.real_name == test_user_details[2]
    assert user1.user_type == "standard"
    assert user1.email == test_user_details[4]
    assert user1.description == test_user_details[5]
    assert user1.is_admin() == False
    
    
# Create user then change all values to other username
def test_change_values_1():
    user1 = ServerUser(*test_user_details)
    user1.username = test_user2_details[0]
    user1.password_hash = test_user2_details[1]
    user1.real_name = test_user2_details[2]
    user1.user_type = test_user2_details[3]
    user1.email = test_user2_details[4]
    user1.description = test_user2_details[5]
    assert user1.username == test_user2_details[0]
    assert user1.password_hash == test_user2_details[1]
    assert user1.real_name == test_user2_details[2]
    assert user1.user_type == test_user2_details[3]
    assert user1.email == test_user2_details[4]
    assert user1.description == test_user2_details[5]
    
# Try invalid entries
# Ensure not changed
def test_change_values_2():
    user1 = ServerUser(*test_user_details)
    user1.username = "        "
    assert user1.username == test_user_details[0]
    user1.username = "short"
    assert user1.username == test_user_details[0]
    user1.username = "user:name1"
    assert user1.username == test_user_details[0]
    user1.username = "user1234$"
    assert user1.username == test_user_details[0]
    user1.username = "!user1234"
    assert user1.username == test_user_details[0]
    user1.username = "user~12345"
    assert user1.username == test_user_details[0]
    
# Try invalid entries
# Ensure not changed
def test_change_values_3():
    user1 = ServerUser(*test_user_details)
    user1.real_name = "Invalid <real> name"
    assert user1.real_name == test_user_details[2]
    user1.real_name = "Invalid : name"
    assert user1.real_name == test_user_details[2]
    user1.real_name = "Invalid 3:al name"
    assert user1.real_name == test_user_details[2]

# Try invalid entries
# Ensure not changed
def test_change_values_4():
    user1 = ServerUser(*test_user_details)
    user1.email = "Invalid<real>@name.com"
    assert user1.email == test_user_details[4]
    user1.email = "Invalid:@name.co.uk"
    assert user1.email == test_user_details[4]
    user1.email = "Invalid 3:al email"
    assert user1.email == test_user_details[4]
    
    
# Try invalid entries
# Ensure not changed
def test_change_values_5():
    user1 = ServerUser(*test_user_details)
    user1.description = "Invalid <scrip> description"
    assert user1.description == test_user_details[5]
    user1.description = "Invalid : description"
    assert user1.description == test_user_details[5]
    user1.description = "Invalid 3:al description"
    assert user1.description == test_user_details[5]
    
    
# Automated test - generate passwords 
# change the password and then see if it passes
def test_passwords_argon2_1():
    user1 = ServerUser(*test_user_details)
    for i in range (num_changes):
        # Set password
        new_password = _create_valid_password()
        # change password
        user1.set_password(new_password, algorithm="Argon2")
        assert user1.check_password(new_password)

# Automated test - generate passwords 
# change the password and then see if it passes
def test_passwords_sha256_1():
    user1 = ServerUser(*test_user_details)
    for i in range (num_changes):
        # Set password
        new_password = _create_valid_password()
        # change password
        user1.set_password(new_password, algorithm="SHA256")
        assert user1.check_password(new_password)

# Test empty password 
# This class will accept, although flask code won't
def test_passwords_empty_1():
    user1 = ServerUser(*test_user_details)
    user1.set_password("")
    assert user1.check_password("")

# does not apply full rules, so simplified valid passwords
def _create_valid_password (max_chars = 20):
    # First create totally random string
    password = ''.join(random.choice(allowed_chars) for i in range(random.randint(1,max_chars)))
    return password