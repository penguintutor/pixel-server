import sys
from serveruser import ServerUser
# Create admin user and password
# Run using:
# python3 createadmin.py <username> <password> >>users.cfg
## Warning!! without two >> then it may delete all existing users.
# Username should not already exist, otherwise will be ignored
# Uses minimal information - login to update afterwards

# Check command line arguments
if (len(sys.argv) < 2):
    print ("Insufficient arguments\npython3 createadmin.py <username> <password> >> users.cfg\n")
    sys.exit()
# check for colon in username
if (':' in sys.argv[1]):
    print ("Colon not allowed in username")
    sys.exit()
# Create user entry
print ("{}:{}:Admin user:admin::\n".format(sys.argv[1], ServerUser.hash_password(sys.argv[2])))
    