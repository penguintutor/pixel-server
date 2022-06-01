# Class to add authentication for Maker IOT projects

import ipaddress
import datetime


class ServerAuth ():
    
    def __init__ (self, auth_filename, users_filename, log_filename):
        self.config_filename = auth_filename
        self.users_filename = users_filename
        self.log_filename = log_filename
        self.error_msg = ""              # Add any error messages for reporting
        self.network_allow_always = []          # list of allowed network addresses which don't require authentication (normally this is local addresses only)
        self.network_allow_auth = []            # as above, but does require authentication (normally this is 0.0.0.0 = allow all, but with authentication) 
        
        # Load the config file - this will include any network authorizations
        success = self.load_config (self.config_filename)
        if (success == 0):
            print ("No authentication config file "+self.config_filename)
        elif (success < 1):
            print ("Error loading authentication config file "+self.config_filename)
            print (self.error_msg)
            
        # Open log file for appending
        self.log_file = open (log_filename, 'a'):
            self.log_file.write(str(datetime.now())+" Authentication loaded\n")
            
            

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
        
    # checks for valid username and password and if so login
    # return True for success or False for fail login
    def login_user (self, username, password):
        if (username == "stewart"):
            if(password == "test"):
                self.log_file.write (str(datetime.now())+" Login success "+username+"\n")
                return True
            else:
                self.log_file.write (str(datetime.now())+" Login failed incorrect password "+username+"\n")
        self.log_file.write (str(datetime.now())+" Login failed invalid username "+username+"\n")
        return False
    # https://www.askpython.com/python-modules/flask/flask-sessions
           
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
                self.log_file.write (str(datetime.now())+" Allow "+auth_type+" "+this_network+"\n")
            except:
                self.log_file.write (str(datetime.now())+" Invalid network "+auth_type+" "+this_network+"\n")
                print ("Not a valid network address "+this_network+"\n")
                
        #print (auth_type + " " + str(auth_list))
        
	
	# check network address against allow_always and allow_auth
	# returns "always", "auth" or "none"
    def check_network (self, ip_address):
	    ip_addr = ipaddress.ip_address(ip_address)
	    
	    # Start log entry
	    self.log_file.write (str(datetime.now()) + " Network auth address: " + ip_address)
	    
	    # check for always first
	    for this_network in self.network_allow_always:
	        # special case check for 0.0.0.0 - which always passes
	        if (ipaddress.ip_address("0.0.0.0") in this_network):
	            self.log_file.write (" always (global)\n")
	            return (" always")
	        elif ip_addr in this_network:
	            self.log_file.write (" always\n")
	            return (" always")
	    # check for always first
	    for this_network in self.network_allow_auth:
	        # special case check for 0.0.0.0 - which always passes
	        if (ipaddress.ip_address("0.0.0.0") in this_network):
	            self.log_file.write (" auth (global)\n")
	            return ("auth")
	        elif ip_addr in this_network:
	            self.log_file.write (" auth\n")
	            return ("auth")
	    self.log_file.write ("none\n")
	    return ("none")
	    
	    
	