from argon2 import PasswordHasher
import hashlib
import uuid

class ServerUser ():
                                                   
    # init with all details
    def __init__ (self, username, password_hash, real_name, user_type, email, description):
        self.username = username
        self.password_hash = password_hash
        self.real_name = real_name
        self.user_type = user_type
        self.email = email
        self.description = description

    # return formatted for writing to file
    def colon_string(self):
	    return "{}:{}:{}:{}:{}:{}".format(self.username, self.password_hash, self.real_name, self.user_type, self.email, self.description)
	
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
	    if self.user_type == "admin":
	        return True
	    return False
	    
    # returns string with the hashed password
    # uses argon2 which is a strong hash, but takes approx 8 seconds 
    # on a Pi Zero - or sha256 which is faster, particularly on Pi Zero
    @staticmethod
    def hash_password (password, algorithm="Argon2"):
        #password_bytes = bytes(password, 'utf-8')
        if algorithm == "SHA256":
            salt = uuid.uuid4().hex
            return "$5$" + salt + "$" + hashlib.sha256(salt.encode() + password.encode()).hexdigest()
        else:
            ph = PasswordHasher()
            return ph.hash(password)
            
        
