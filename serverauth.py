# Class to add authentication for Maker IOT projects

import ipaddress
from datetime import datetime
import logging
from serveruser import ServerUser


# network config file is only loaded initially (needs reload)
# user config file is checked each time so that any changes
# to the user config file are immediately available

class ServerAuth ():
    
    def __init__ (self, auth_filename, users_filename):
        self.config_filename = auth_filename
        self.users_filename = users_filename
        self.error_msg = ""              # Add any error messages for reporting
        self.network_allow_always = []          # list of allowed network addresses which don't require authentication (normally this is local addresses only)
        self.network_allow_auth = []            # as above, but does require authentication (normally this is 0.0.0.0 = allow all, but with authentication
        
        # Load the config file - this will include any network authorizations
        success = self.load_config (self.config_filename)
        if (success == 0):
            #print ("No authentication config file "+self.config_filename)
            logging.warning("No authentication config file "+ self.config_filename)
        elif (success < 1):
            #print ("Error loading authentication config file "+self.config_filename)
            #print (self.error_msg)
            logging.error("Error loading config file "+ self.config_filename)

        logging.info("Authentication loaded")
            


    # load config if it exists
    # If not exist return 0, if successful return 1, if not successful return -1 (file error) -2 (data error)
    # After error stop reading rest of file
    # If error also populate self.error_msg
    # Includes some validation checks, but these are very crude
    # to detect mistakes rather than security reasons
    def load_config(self, filename):
        # Try and open file - if not exist then just return
        try:
            with open (filename, "r") as cfg_file:
                lines = cfg_file.readlines()
                for line in lines:
                    # remove training / leading chars
                    line = line.strip()
                    # If comment or blank line ignore
                    if (line.startswith('#') or len(line) < 1):
                        continue
                    # split based on =
                    (key, value) = line.split('=', 1)
                    # strip any spaces
                    key = key.strip()
                    value = value.strip()
                    # validate value and store
                    if (key == "network_allow_always"):
                        self.update_network("always", value)
                    elif (key == "network_allow_auth"):
                        self.update_network("auth", value)

	    # File not found 
        except FileNotFoundError:
            self.errormsg = "File not found "+filename
            return 0
        # Other file read error
        except OSError:
            self.errormsg = "Error reading file "+filename
            return -1
            
        return 1
       
        
    # Loads the information about a single user and returns as
    # ServerUser object, otherwise returns None
    def load_user (self, user_filename, username):
        try:
            with open(user_filename) as read_file:
                for line in read_file:
                    this_line = line.strip()
                    # check if comment in which case skip
                    if (this_line.startswith("#")):
                        continue
                    # split line into fields
                    user_elements = this_line.split(":", 5)
                    # If not this user then skip
                    if user_elements[0] != username:
                        continue
                    return ServerUser(*user_elements)
        except Exception as e: 
            logging.warning ("Error reading users file "+ user_filename+" "+str(e))
        # User not found return None
        return None
        
    # checks for valid username and password and if so login
    # return True for success or False for fail login
    # IP Address is required. Does not do additional authentication, but used for logging purposes
    def login_user (self, username, password, ip_address):
        # Check username does not include colon
        if ':' in username: 
            logging.warning (ip_address+" Login failed username contains colon "+username)
            return False
        this_user = self.load_user (self.users_filename, username)
        if this_user == None:
            # Could also be corrupt file or similar, but most likely invalid username - check log for corrupt file error
            logging.warning (ip_address+" Login failed invalid username "+username)
            return False
        if (this_user.check_password (password)):
            logging.info (ip_address+" Login success "+username)
            return True
        else:
            logging.warning (ip_address+" Login failed incorrect password "+username)
        return False
           
    def update_network (self, auth_type, network_string):
        # auth_type determines which list we are updating
        if (auth_type == "always"):
            auth_list = self.network_allow_always
        elif (auth_type == "auth"):
            auth_list = self.network_allow_auth
        else: 
            return 
        # split based on commas
        for this_network in network_string.split(","):
            try:
                auth_list.append(ipaddress.ip_network(this_network))
                logging.info ("Allow "+auth_type+" "+this_network)
            except:
                logging.info ("Invalid network "+auth_type+" "+this_network)
                #print ("Not a valid network address "+this_network+"\n")
                
        #print (auth_type + " " + str(auth_list))
        
	
	# check network address against allow_always and allow_auth
	# returns "always", "auth" or "none"
    def check_network (self, ip_address):
	    ip_addr = ipaddress.ip_address(ip_address)
	    
	    log_string = "Network auth address: " + ip_address
	    
	    # check for always first
	    for this_network in self.network_allow_always:
	        # special case check for 0.0.0.0 - which always passes
	        if (ipaddress.ip_address("0.0.0.0") in this_network):
	            logging.info(log_string+" always (global)")
	            return ("always")
	        elif ip_addr in this_network:
	            logging.info(log_string+" always")
	            return ("always")
	    # check for always first
	    for this_network in self.network_allow_auth:
	        # special case check for 0.0.0.0 - which always passes
	        if (ipaddress.ip_address("0.0.0.0") in this_network):
	            logging.info(log_string+" auth (global)")
	            return ("auth")
	        elif ip_addr in this_network:
	            logging.info(log_string+" auth")
	            return ("auth")
	    logging.info(log_string+"none\n")
	    return ("none")
	    
	    
	