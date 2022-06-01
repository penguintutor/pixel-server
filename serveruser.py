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
    def file_format(self):
	    return "{}:{}:{}:{}:{}:{}\n".format(self.username, self.password_hash, self.real_name, self.user_type, self.email, self.description)

	    