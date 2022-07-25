#!/usr/bin/env python3
import time
#from flask import Flask
from flask import request
from flask import render_template
from flask import session
from flask import redirect
from flask import Markup
#from flask_wtf.csrf import CSRFProtect
from rpi_ws281x import *
import threading
import logging, os
#import random
#import string
from pixelserver.pixelconfig import PixelConfig
from pixelserver.pixelseq import PixelSeq, SeqList
from pixelserver.statusmsg import StatusMsg
from pixelserver.customlight import CustomLight
from pixelserver.serverauth import ServerAuth
from pixelserver.serveruseradmin import ServerUserAdmin

# 
# # Custom settings - filenames with further configs
# auth_config_filename = "auth.cfg"
# auth_users_filename = "users.cfg"
# default_config_filename = "defaults.cfg" 
# custom_config_filename = "pixelserver.cfg"
# custom_light_config_filename = "customlight.cfg"
# log_filename = "/var/log/pixelserver.log"

# Turn on logging through systemd
#logging.basicConfig(level=logging.INFO, filename=log_filename, filemode='a', #format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
#logging.info ("PixelServer application start")

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

#csrf = CSRFProtect()
#app = Flask(
#    __name__,
#    template_folder="www"
#    )
# Create a secret_key to last whilst the program is running
#app.secret_key = ''.join(random.choice(string.ascii_letters) for i in range(15))
#csrf.init_app(app)


# check authentication using network and user
# return "network", "logged_in", "login_required" or "invalid" (invalid = network rules prohibit)
def auth_check (ip_address):
    auth_type = auth.check_network(ip_address)
    # Also need to authenticate
    if auth_type == "always" or auth_type=="auth":
        # even if also check for logged in useful for admin logins
        if 'username' in session:
            return "logged_in"
        elif (auth_type == "network"):
            return "network"
        else: 
            return "login_required"
    return "invalid"




#def flaskThread():
#    app.run(host='0.0.0.0', port=80)
    
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


# Gets IP address - supports proxy headers or normal network
def get_ip_address():
    # Start by setting ip address to the real address
    ip_address = request.remote_addr
    if 'X-Real-IP' in request.headers and auth.check_proxy(ip_address):
        proxy_addr = ip_address
        ip_address = request.headers.get('X-Real_IP')
        logging.info("Proxy connection {} is {}".format(proxy_addr, ip_address))
    return ip_address
    
# checks that network is allowed and user is an admin
# on success return "admin"
# On fail could be "invalid" (not allowed), "login" (not logged in), "notadmin" (logged in as standard user)
def check_permission_admin ():
    # check address first
    ip_address = get_ip_address()
    login_status = auth_check(ip_address)
    if login_status == "invalid": 
        return "invalid"
    # Not logged in
    if not (login_status == "logged_in") :
        return "login"
    # Get username and check user is admin
    username = session['username']
    if not (auth.check_admin(username)):
        return "notadmin"
    return "admin"

   
    
# Also converts to the format used by ServerUser 
# eg. real_name instead of realname which is used in form
# Any errors return with error dict instead
def parse_form (user_admin, form_data):
    data_dict = {}
    
    # Check for change in username, only add to dict if different to currentusername
    # Does not check that the new username is not duplicate - check that later
    if 'currentusername' in form_data.keys() and 'username' in form_data.keys():
        if form_data['currentusername'] != form_data['username']:
            # check that the new username is not blank
            requested_username = form_data['username'].strip()
            if requested_username == "":
                return {'error': "Username cannot be blank"}
            # only allow alphanumeric
            check_user = user_admin.validate_user(requested_username)
            if check_user[0] != True:
                return {"error": check_user[1]}
            # is valid so update dict
            data_dict['username'] = form_data['username']
            
                
    
    if 'realname' in form_data.keys():
        # reject if a colon (potential attack)
        if ':' in form_data['realname']:
            return {'error': "Invalid character in name"}
        # strip any tags
        data_dict['real_name'] = Markup(form_data['realname']).striptags()
        
    # Admin is used to set usertype
    # convert at this stage to usertype
    if 'admin' in form_data.keys():
        #if form_data['admin'] == True:
        data_dict['user_type'] = "admin"
    # If not in form then it's false
    else:
        data_dict['user_type'] = "standard"
            
    if 'email' in form_data.keys():
        # Does not validate it's actually an email string
        # just check for not allowed tags
        # strip : and html tags
        if ':' in form_data['email']:
            return {'error': "Invalid character in email address"}
        # strip any tags
        data_dict['email'] = Markup(form_data['email']).striptags()

    if 'description' in form_data.keys():
        # strip : and html tags
        if ':' in form_data['description']:
            return {'error': "Invalid character in description"}
        # strip any tags
        data_dict['description'] = Markup(form_data['description']).striptags()
        
    return data_dict


if __name__ == "__main__":
    # run as two threads - main thread and flask thread
    mt = threading.Thread(target=mainThread)
    ft = threading.Thread(target=flaskThread)
    mt.start()
    ft.start()

