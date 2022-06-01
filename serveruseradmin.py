from serveruser import ServerUser
from hashlib import blake2b


# File format - colon seperated (colon not allowed in any of the fields)
# username:password:real name:usertype:email:description
# Description could be comments about the user type
# Lines can start with a # to comment - otherwise all entries must be valid
# Note that user added comments will be discarded when next saved



# Class to administer users - holds all users on system
# Designed for small number of users in a typical IOT system
# For servers with lots of users then replace this with database driven version
# Returns True for success - False if there is a problem (eg. file not exist)
class ServerUserAdmin():

    def __init__ (self, usersfile):
        self.filename = usersfile
        # List of users on system - Entries in this list should not be updated directly
        # instead update within this class so that it saves any changes
        self.users = {}
        # track if the file loads successfully (can use other code to check)
        self.file_loaded = False
        # loads users - if fails then return false
        if self.load_users() == True and len(self.users) > 0:
            self.file_loaded = True
        

    def load_users (self):
        try:
            with open(self.filename) as read_file:
                for line in read_file:
                    this_line = line.strip()
                    # check if comment in which case skipt
                    if (this_line.startswith("#")):
                        continue
                    # split line into fields
                    user_elements = this_line.split(":", 5)
                    # load as a class object
                    try :
                        # make sure doesn't already exist - first entry is kept
                        # should not happen as saved from a dictionary
                        if user_elements[0] in self.users.keys():
                            print ("Warning duplicate user entry "+user_elements[0])
                        else:
                            self.users[user_elements[0]] = ServerUser(*user_elements)
                    except:
                        # If corrupt file then just exit as can't trust to be safe
                        print ("Corrupt file - invalid entry in "+self.filename)
                        return False
        except FileNotFoundError:
            print ("Error file not found "+self.filename)
            return False
        except OSError:
            print ("Error file read error "+self.filename)
            return False
        except Exception as e:
            print ("Unknown error reading file "+self.filename+" "+str(e))
            return False
        # Success
        return True

    # Replaces existing user file with new user file
    def save_users (self):
        try:
            with open(self.filename, "w") as write_file:
                for this_user in self.users.values():
                    write_file.write(this_user.file_format())
        except Exception as e:
            print ("Error saving file to "+self.filename+" "+str(e))
            return False
        return True

    # When adding a new user then password is plain text in format that the
    # user added - this performs the conversion to hash
    # returns string - "success", "duplicate" (if username duplicate), "invalid" (eg. if ":" in a field)
    def add_user (self, username, password_text, real_name, user_type, email, description):

        # check it doesn't already exist first (based on username):
        if username in self.users.keys():
            return "duplicate"

        password_hash = self.hash_password (password_text)
        
        # create the entry
        self.users[username] = ServerUser(username, password_hash, real_name, user_type, email, description)
        
        # save the changes 
        self.save_users()



    def user_exists (self, username):
        if username in self.users.keys():
            return True
        return False


    # returns string with the hashed password
    # uses blake2b
    def hash_password (self, password):
        password_bytes = bytes(password, 'utf-8')
        hash_alg = blake2b()
        hash_alg.update(password_bytes)
        return hash_alg.hexdigest()


    def check_username_password (self, username, password):
        # Check username exists
        if not username in self.users.keys():
            return False
        # check password hash
        if (self.hash_password(password) == self.users[username].password_hash):
            return True
        # If password fail then return false
        else: 
            return False
