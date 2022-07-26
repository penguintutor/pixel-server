from argon2 import PasswordHasher
import hashlib
import uuid


class ServerUser ():
                                                   
    # init with all details
    # all values are set as internal and need to be updated
    # using getters / setters (includes security features)
    def __init__ (self, username, password_hash, real_name, user_type, email, description):
        self._username = username
        self.password_hash = password_hash
        self._real_name = real_name
        self._user_type = user_type
        self._email = email
        self._description = description
        
        
    # Getters and setters
    ## These include security checks, but is not user friendly - just ignores request
    ## Checks should be performed higher up the request, but this is a final catch alll
    
    @property
    def username(self):
        return self._username
        
    @username.setter
    def username(self, new_username):
        # check it doesn't have : etc.
        if ":" in new_username:
            return
        # strip whitespace and check not empty username
        new_username = new_username.strip()
        if new_username == "":
            return
        # Only allow alpha numeric
        if not new_username.isalnum():
            return
        if len(new_username) < 6 :
            return
        # checks complete - update username
        self._username = new_username
        
    # password property
    # password cannot be returned as it's stored as a hash
    # If requested just return asterix *********
    @property
    def password(self):
        return "********"
        
    # Setting a new password will result in it converted to a hash
    # Does not check minimum length / other password requirements
    # Using this does not give control over algorith - instead use set_password
    @password.setter
    def password(self, new_password):
        self.set_password (new_password)
    
    # This is recommended way to set password
    def set_password (self, new_password, algorithm="Argon2"):
        self.password_hash = ServerUser.hash_password (new_password, algorithm)
            
    @property
    def real_name(self):
        return self._real_name
        
    @real_name.setter
    def real_name(self, new_name):
        # check it doesn't have : or < > 
        if ":" in new_name or "<" in new_name or ">" in new_name:
            return
        # strip whitespace
        new_name = new_name.strip()
        # Save
        self._real_name = new_name
        
    @property
    def user_type(self):
        return self._user_type
        
    @user_type.setter
    def user_type(self, new_type):
        if new_type == "admin":
            self._user_type = "admin"
        elif new_type == "standard":
            self._user_type = "standard"
            
    @property
    def email(self):
        return self._email
        
    @email.setter
    def email(self, new_email):
        # basic checks for : and <>
        if ":" in new_email or "<" in new_email or ">" in new_email:
            return
        self._email = new_email
        
    @property
    def description(self):
        return self._description
        
    @description.setter
    def description(self, new_description):
        # basic checks for : and <>
        if ":" in new_description or "<" in new_description or ">" in new_description:
            return
        self._description = new_description


    # return formatted for writing to file
    def colon_string(self):
	    return "{}:{}:{}:{}:{}:{}".format(self._username, self.password_hash, self._real_name, self._user_type, self._email, self._description)
	    

    # Checks plaintext password against stored password hash
    def check_password (self, password):
        # check for $5$ = SHA256
        if self.password_hash[0:3] == "$5$":
            salt, just_hash = self.password_hash[3:].split('$')
            hashed_given_password = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
            return hashed_given_password == just_hash
        else:
            ph = PasswordHasher()
            # Invalid password raises exception - catch and return false
            try:
                if ph.verify(self.password_hash, password):
                    return True
            except:
                return False
        # Shouldn't get this but in case changes in future
        return False
	    
    def is_admin(self):
	    if self._user_type == "admin":
	        return True
	    return False
	    
    # returns string with the hashed password
    # uses argon2 which is a strong hash, but takes approx 8 seconds 
    # on a Pi Zero - or sha256 which is faster, particularly on Pi Zero
    @staticmethod
    def hash_password (password, algorithm="Argon2"):
        if algorithm == "SHA256":
            salt = uuid.uuid4().hex
            return "$5$" + salt + "$" + hashlib.sha256(salt.encode() + password.encode()).hexdigest()
        else:
            ph = PasswordHasher()
            return ph.hash(password)
            
        
