#!/usr/bin/env python3
import time
from flask import Flask
from flask import request
from flask import render_template
from flask import session
from rpi_ws281x import *
import threading
import random
import string
from pixelconfig import PixelConfig
from pixelseq import PixelSeq, SeqList
from statusmsg import StatusMsg
from customlight import CustomLight
from serverauth import ServerAuth


# Custom settings - filenames with further configs
auth_config_filename = "auth.cfg"
auth_users_filename = "users.cfg"
log_filename = "pixelserver.log"        # currently used for authentication logging
default_config_filename = "defaults.cfg" 
custom_config_filename = "pixelserver.cfg"
custom_light_config_filename = "customlight.cfg"

# Globals for passing information between threads
# needs default settings
upd_time = time.time()
seq_set = {
    "sequence" : "alloff",
    "delay" : 900,
    "reverse" : 0,
    "colors" : "ffffff"
    }

# used for toggle option
# Ignored unless toggle=True parameter
on_status = False

# List of sequences
seq_list = SeqList()

app = Flask(
    __name__,
    template_folder="www"
    )
# Create a secret_key to last whilst the program is running
app.secret_key = ''.join(random.choice(string.ascii_letters) for i in range(15))

auth = ServerAuth(auth_config_filename, auth_users_filename, log_filename)

# check authentication using network and user
# return "network", "logged_in", "login_required" or "invalid" (invalid = network rules prohibit)
def auth_check ():
    auth_type = auth.check_network(request.remote_addr)
    # Also need to authenticate
    if auth_type == "always":
        return "network"
    elif auth_type == "auth":
        if 'username' in session:
            return "logged_in"
        # otherwise not authenticated
        else: 
            return "login_required"
    return "invalid"


@app.route("/")
def main():
    login_status = auth_check()
    # not allowed even if logged in
    if login_status == "invalid":
        return render_template('invalid.html')
    elif login_status == "network" or login_status == "logged_in":
        return render_template('index.html')
    else:   # login required
        return render_template('login.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (auth.login_user(username, password) == True):
            # create session
            session['username'] = username
            return render_template('index.html')
    # Reach here then login was not successful
    return render_template('login.html')
    
@app.route("/logout")
def logout():
    # Don't log logouts
    session.pop('username', None)
    return render_template('login.html')

@app.route("/pixels.css")
def css():
    return render_template('pixels.css'), 200, {'Content-Type': 'text/css; charset=utf-8'}

@app.route("/pixels.js")
def js():
    return render_template('pixels.js'), 200, {'Content-Type': 'text/javascript; charset=utf-8'}
    
@app.route("/jquery.min.js")
def jquery():
    return render_template('jquery.min.js'), 200, {'Content-Type': 'text/javascript; charset=utf-8'}
   
@app.route("/jquery-ui.min.js")
def jqueryui():
    return render_template('jquery-ui.min.js'), 200, {'Content-Type': 'text/javascript; charset=utf-8'}
    
# provides list of sequences - don't authenticate
@app.route("/sequences.json")
def seqJSON ():
    return (seq_list.json())
    
@app.route("/set")
def setSeq():
    global seq_set, upd_time, on_status
    status = StatusMsg()
    status.set_server_values(seq_set)
    new_values = {}
    # perform first stage validation on data sent
    this_arg = request.args.get('seq', default = 'alloff', type = str)
    if (seq_list.validate_sequence(this_arg) == True):
        new_values["sequence"] = this_arg
    else:
        status.set_status ("error", "Invalid request")
        return status.get_message()
    this_arg = request.args.get('delay', default = 1000, type = int)
    if (this_arg >= 0 and this_arg <= 1000):
        new_values["delay"] = this_arg
    else:
        status.set_status ("error", "Invalid delay")
        return status.get_message()
    this_arg = request.args.get('reverse', default = '0', type = str)
    if (this_arg == "1"):
        new_values["reverse"] = True
    else:
        new_values["reverse"] = False
    this_arg = request.args.get('colors', default = '#ffffff', type = str)
    if (seq_list.validate_color_string(this_arg)):
        new_values["colors"] = this_arg
    else:
        status.set_status ("error", "Invalid colors")
        return status.get_message()
    # If reach here then it was successful for copy temp dict to actual
    seq_set = new_values
    
    # Check for toggle status - if on and toggle=true then turn off
    # this is done afer seq_set is copied - so override seq_set 
    this_arg = request.args.get('toggle', default = 'False', type = str)
    # only handle if toggle="True", otherwise ignore the parameter
    if (this_arg == "True" or this_arg == "true"):
        if (on_status == True):
            # Override request and replace with AllOff
            seq_set["sequence"] = "alloff" 
            on_status = False
        else:
            # Action as normal, but set to true
            on_status = True
            
    # Update successful status
    status.set_server_values(seq_set)
    status.set_status ("success")
        
    # update time to notify other thread it's changed
    upd_time = time.time()
    return status.get_message ()

def flaskThread():
    app.run(host='0.0.0.0', port=80)
    
# Setup pixel strip and then start the updatePixels loop
def mainThread():
    global seq_set, upd_time, pixel_conf

    
    last_update = upd_time
    current_sequence = ""
    pixel_conf = PixelConfig(default_config_filename, custom_config_filename, custom_light_config_filename)
    pixels = PixelSeq(pixel_conf)
    
    # Use for custom color lights (eg CheerLights)
    custom_light = CustomLight(pixel_conf.customlightcfg)
    
    sequence_position = 0
    colors = [Color(255,255,255)]

    
    while(1):
        # Check for change in custom light colors
        # Reloads files if updated
        if custom_light.is_updated():
            upd_time = time.time()
        
        # If updated sequence / value etc.
        if (upd_time != last_update) :
            # convert colors to list instead of comma string
            color_list = seq_set['colors'].split(",")
            # handle custom colors
            color_list = custom_light.subs_custom_colors(color_list)   
            # Convert color string to list of colors (pre formatted for pixels)
            # Value returned as seq_colors is a list of Colors(), but may also include "custom" for any custom colors
            colors = seq_list.string_to_colors(color_list)
                     
            # If sequence changed then reset seq_position
            if (seq_set['sequence'] != current_sequence):
                sequence_position = 0
                current_sequence = seq_set['sequence']

        # returns sequence_position which is used for future calls
        sequence_position = pixels.updateSeq(
            seq_set['sequence'],
            sequence_position,
            seq_set['reverse'],
            colors) 
        last_update = upd_time
        # Sleep used for delay this means that there will be that long a delay between updates
        time.sleep(seq_set['delay']/1000)

if __name__ == "__main__":
    # run as two threads - main thread and flask thread
    mt = threading.Thread(target=mainThread)
    ft = threading.Thread(target=flaskThread)
    mt.start()
    ft.start()

