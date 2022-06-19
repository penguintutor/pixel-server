from serveruser import ServerUser

# File format - colon seperated (colon not allowed in any of the fields)
# username:password:real name:usertype:email:description
# Description could be comments about the user type
# Lines can start with a # to comment - otherwise all entries must be valid
# Note that user added comments will be discarded when next saved



# Class to administer users - holds all users on system
# Designed for small number of users in a typical IOT system
# For servers with lots of users then replace this with database driven version
# Returns True for success - False if there is a problem (eg. file not exist)
# Algorithm is used for adding new users only - currently support "argon2" or "sha256" - argon2 is much more secure but takes longer
# may be too slow for some systems
class ServerUserAdmin():

    def __init__ (self, usersfile, algorithm="argon2"):
        self.filename = usersfile
        # List of users on system - Entries in this list should not be updated directly
        # instead update within this class so that it saves any changes
        self.users = {}
        # track if the file loads successfully (can use other code to check)
        self.file_loaded = False
        # loads users - if fails then return false
        if self.load_users() == True and len(self.users) > 0:
            self.file_loaded = True
        self.algorithm = algorithm
        

    def load_users (self):
        try:
            with open(self.filename) as read_file:
                for line in read_file:
                    this_line = line.strip()
                    # skipt empty line
                    if (this_line == ""):
                        continue
                    # check if comment in which case skip
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
                    except Exception as e:
                        # If corrupt file then just exit as can't trust to be safe
                        print ("Corrupt file - invalid entry in "+self.filename)
                        print (str(e))
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
        
    def delete_user(self, username):
        del self.users[username]

    # Replaces existing user file with new user file
    def save_users (self):
        try:
            with open(self.filename, "w") as write_file:
                for this_user in self.users.values():
                    write_file.write(this_user.colon_string()+"\n")
        except Exception as e:
            print ("Error saving file to "+self.filename+" "+str(e))
            return False
        return True

    # When adding a new user then password is plain text in format that the
    # user added - this performs the conversion to hash
    # returns string - "success", "duplicate" (if username duplicate), "invalid" (eg. if ":" in a field)
    # minimum is username and password - rest optional
    def add_user (self, username, password_text, real_name="", user_type="standard", email="", description=""):

        # check it doesn't already exist first (based on username):
        if username in self.users.keys():
            return "duplicate"
            
        # Security check - ensure that none of the fields include a colon
        # Further checks could be added (check for valid email address etc.)
        # Password is allowed a colon as that is converted into a hash which will be colon free
        # Could also convert colon to other character if required
        if (':' in username or ':' in real_name or 
            ':' in user_type or ':' in email or ':' in description):
            return "invalid"

        password_hash = ServerUser.hash_password (password_text, self.algorithm)
        
        # create the entry
        self.users[username] = ServerUser(username, password_hash, real_name, user_type, email, description)
        
        # save the changes 
        self.save_users()
        return "success"


    def user_exists (self, username):
        if username in self.users.keys():
            return True
        return False

    def check_admin (self, username):
        if username in self.users.keys() and self.users[username].user_type == "admin":
            return True
        return False
        
    def num_users(self):
        return len(self.users)

    def check_username_password (self, username, password):
        # Check username exists
        if not username in self.users.keys():
            return False
        # check password
        if (self.users[username].check_password(password)):
            return True
        # If password fail then return false
        else: 
            return False

    # New user form starts with username - as long as that is unique then 
    # creates a basic entry and then goes to edit for rest of details
    def html_new_user (self):
        html_string = ""
        # Create form
        html_string += "<input type=\"hidden\" name=\"newuser\" value=\"newuser\">\n"
        html_string += "<label for=\"username\">Username:</label>\n"
        html_string += "<input type=\"text\" id=\"username\" name=\"username\" value=\"\"><br />\n"
        return html_string
        
    # Stage 2 of add new user - add password
    def html_new_user_stage2 (self, username):
        # Check user doesn't already exist
        # Should have already checked - but additional check
        if self.user_exists(username):
            return ("User already exists")
        html_string = ""
        # Create form
        html_string += "<input type=\"hidden\" name=\"newuser\" value=\"userpassword\">\n"
        html_string += "<label for=\"username\">Username:</label>\n"
        html_string += "<input type=\"text\" id=\"username\" name=\"username\" value=\"{}\" readonly><br />\n".format(username)
        html_string += "<label for=\"password\">Password:</label>\n"
        html_string += "<input type=\"password\" id=\"password\" name=\"password\" value=\"\"><br />\n"
        html_string += "<label for=\"password2\">Repeat password:</label>\n"
        html_string += "<input type=\"password\" id=\"password2\" name=\"password2\" value=\"\"><br />\n"

        return html_string
        
    # Add any specific rules (eg. special char / capitals)
    # Minimum length = 8, minimum 1 alpha & 1 number
    # No need to try and strip any chars as the password
    # will be hashed
    def validate_password (self, password):
        if len(password) < 8:
            return (False, "Password must be at least 8 characters long")
        if self.has_digit(password) and self.has_alpha(password):
            return (True, "")
        else:
            return (False, "Password must contain at least one letter and one digit")
            
            
    def has_digit (self, string):
        for i in list(string):
            if i.isdigit():
                return True
        return False

    def has_alpha (self, string):
        for i in list(string):
            if i.isalpha():
                return True
        return False

    # Checks to see if user is valid (min 6 chars - alphanumeric)
    def validate_user (self, username):
        if len(username) < 6: 
            return (False, "Username must be minimum of 6 characters")
        if username.isalnum():
            return (True, "")
        else:
            return (False, "Username must be letters and digits only")

    def html_edit_user (self, username):
        html_string = ""
        # Check user exists
        if not username in self.users:
            return "Invalid user selected\n"
        this_user = self.users[username]
        # Create form
        html_string += "<input type=\"hidden\" name=\"edituser\" value=\"edituser\">\n"
        html_string += "<input type=\"hidden\" name=\"currentusername\" value=\"{}\">\n".format(this_user.username)
        html_string += "<label for=\"username\">Username:</label>\n"
        html_string += "<input type=\"text\" id=\"username\" name=\"username\" value=\"{}\"><br />\n".format(this_user.username)
        # Does not change password - that has to be done separately
        html_string += "<label for=\"realname\">Name:</label>\n"
        html_string += "<input type=\"text\" id=\"realname\" name=\"realname\" value=\"{}\"><br />\n".format(this_user.real_name)
        # Admin checkbox = user_type
        html_string += "<label for=\"admin\">Admin:</label>\n"
        if (this_user.user_type == "admin"):
            html_string += "<input type=\"checkbox\" name=\"admin\" checked=\"checked\"><br />\n"
        else:
            html_string += "<input type=\"checkbox\" name=\"admin\"><br />\n"
        html_string += "<label for=\"email\">Email:</label>\n"
        html_string += "<input type=\"text\" id=\"email\" name=\"email\" value=\"{}\"><br />\n".format(this_user.email)
        html_string += "<label for=\"description\">Description:</label>\n"
        html_string += "<input type=\"text\" id=\"description\" name=\"description\" value=\"{}\"><br />\n".format(this_user.description)
        return html_string
            
        
    # Returns all users as a html table entries (does not include table / th)
    # Links to useradmin - with action = "delete" or "edit"
    def html_table_all (self):
        html_string = ""
        for userkey, uservalue in self.users.items():
            html_string += "<tr><td><a href=\"useradmin?user="+userkey+"&action=edit\">"+userkey+"</a></td>"
            html_string += "<td>"+uservalue.real_name+"</td>"
            html_string += "<td>"+uservalue.user_type+"</td>"
            html_string += "<td>"+uservalue.email+"</td>"
            html_string += "<td><a href=\"useradmin?user="+userkey+"&action=delete\">X</a></td></tr>\n"
        return html_string
            
        

