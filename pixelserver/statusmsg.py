import json

class StatusMsg():
    def __init__(self):
        self.status = {
            # default to error - change if successful success
            # relates to current request - not status of server
            'status' : "error",
            # sequence
            'sequence' : "",
            # string for message
            'msg' : ""
            }
            
    # Set based on current server values (may need to call later if successful)
    def set_server_values (self, seq_status):
        for key, value in seq_status.items():
            self.status[key] = value
        
            
    def set_status (self, status_value, msg=""):
        self.status['status'] = status_value
        self.status['msg'] += msg
    
    def get_message(self):
        return self.get_json()
        
    def get_json(self):
        return json.dumps(self.status)
