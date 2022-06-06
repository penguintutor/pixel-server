from argon2 import PasswordHasher

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
        ph = PasswordHasher()
        # Invalid password raises exception - catch and return false
        try:
            if ph.verify(self.password_hash, password):
                return True
        except:
            return False
        # Shouldn't get this but in case changes in future
        return False
	    
	    
    # returns string with the hashed password
    # uses argon2 which is a strong hash, but takes approx 8 seconds 
    # on a Pi Zero - could use a different hash for speed, but would
    # likely be less secure
    @staticmethod
    def hash_password (password):
        password_bytes = bytes(password, 'utf-8')
        ph = PasswordHasher()
        return ph.hash(password)
        
