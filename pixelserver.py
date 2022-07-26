#!/usr/bin/env python3
import pixelserver
from pixelserver import create_app
from pixelserver.pixels import Pixels
import threading

# Custom settings - filenames with further configs
default_config_filename = "defaults.cfg" 
custom_config_filename = "pixelserver.cfg"
custom_light_config_filename = "customlight.cfg"
auth_config_filename = "auth.cfg"
auth_users_filename = "users.cfg"
log_filename = "/var/log/pixelserver.log"

def flaskThread():
    app.run(host='0.0.0.0', port=80)
    
# Setup pixel strip and then start the updatePixels loop
def mainThread():
    pixels.run()
    
app = create_app(auth_config_filename, auth_users_filename, log_filename)
pixels = Pixels(default_config_filename, custom_config_filename, custom_light_config_filename)

if __name__ == "__main__":
    # run as two threads - main thread and flask thread
    mt = threading.Thread(target=mainThread)
    ft = threading.Thread(target=flaskThread)
    mt.start()
    ft.start()


