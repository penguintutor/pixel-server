#!/usr/bin/env python3
import time
from flask import Flask
from flask import request
from flask import render_template
from flask import session
from flask import redirect
from flask import Markup
from rpi_ws281x import *
import threading
import logging, os
import random
import string
from pixelconfig import PixelConfig
from pixelseq import PixelSeq, SeqList
from statusmsg import StatusMsg
from customlight import CustomLight
from serverauth import ServerAuth
from serveruseradmin import ServerUserAdmin


# Custom settings - filenames with further configs
auth_config_filename = "auth.cfg"
auth_users_filename = "users.cfg"
default_config_filename = "defaults.cfg" 
custom_config_filename = "pixelserver.cfg"
custom_light_config_filename = "customlight.cfg"
log_filename = "/var/log/pixelserver.log"

# Turn on logging through systemd
logging.basicConfig(level=logging.INFO, filename=log_filename, filemode='a', format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.info ("PixelServer application start")

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

auth = ServerAuth(auth_config_filename, auth_users_filename)

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


@app.route("/")
@app.route("/home")
def main():
    ip_address = get_ip_address()
    login_status = auth_check(ip_address)
    # not allowed even if logged in
    if login_status == "invalid":
        return redirect('/invalid')
    elif login_status == "network":
        return ('index.html')
    elif login_status == "logged_in":
        # Also check if admin - to show settings button
        username = session['username']
        if (auth.check_admin(username)):
            admin = True
        else:
            admin = False
        return render_template('index.html', user=session['username'], admin=admin)
    else:   # login required
        return redirect('/login')

@app.route("/login", methods=['GET', 'POST'])
def login():
    # Start by setting ip address to the real address
    ip_address = get_ip_address()
    login_status = auth_check(ip_address)
    # check not an unauthorised network
    if login_status == "invalid":
        return redirect('/invalid')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (auth.login_user(username, password, ip_address) == True):
            # create session
            session['username'] = username
            return redirect('/')
        # Reach here then failed login attempt
        return render_template('login.html', message='Invalid login attempt')
    # New visit to login page
    return render_template('login.html')
    
@app.route("/logout")
def logout():
    if 'username' in session:
        username = session['username']
        logging.info("User logged out "+username)
    # pop off the session even if not logged in
    session.pop('username', None)
    return render_template('login.html', message="Logged out")
    
# admin and settings only available to logged in users regardless of 
# network status
@app.route("/settings", methods=['GET', 'POST'])
def settings():
    global pixel_conf
    ip_address = get_ip_address()
    # Status msg for feedback to user
    status_msg = ""
    # Authentication first
    login_status = auth_check(ip_address)
    # not allowed even if logged in
    if login_status == "invalid":
        return redirect('/invalid')
    # Network approval not sufficient for useradmin - must be logged in
    # If not approved then issue login page
    if not (login_status == "logged_in") :
        return redirect('/login')
    # Reach here then this is logged in - also need to check they are admin
    username = session['username']
    if not (auth.check_admin(username)):
        # If trying to do admin, but not an admin then we log them off
        # before allowing them to login again
        session.pop('username', None)
        return render_template('login.html', message='Admin permissions required')
    
    # Reach here logged in as an admin user - update settings and/or display setting options
    if request.method == 'POST':
        #username = session['username']  # needed for logging the action
        
        update_dict = {}
        
        # process the form - validate all parameters
        # Read into separate values to validate all before updating
        for key, value in request.form.items():
            #print ("Key {} Value {}".format(key, value))
            (status, temp_value) = pixel_conf.validate_parameter(key, value)
            #print ("Status {} Value {}".format(status, temp_value))
            # If we get an error at any point - don't save and go back to 
            # showing current status
            if (status == False):
                status_msg = temp_value
                #print (status_msg)
                break
            # Save this for updating values - use returned value
            # in case it's been sanitised (only certain types are)
            update_dict[key] = temp_value
            #print ("Dict updated with {} Value {}".format(key, temp_value))
            
        # special case any checkboxes are only included if checked
        if not ("ledinvert" in request.form.keys()):
            update_dict["ledinvert"] = False
            
                
        # As long as no error save
        if (status_msg == ""):
            for key,value in update_dict.items():
                if (pixel_conf.update_parameter(key, value) == False): 
                    status_msg = "Error updating settings"
                    logging.info("Error updating settings by "+username)
                    
        # Check no error and if so then save
        if not pixel_conf.save_settings():
            status_msg = "Error saving custom config file"
            logging.info("Error saving custom config file")
            
                    
        # As long as still no error then report success
        if (status_msg == ""):
            status_msg = "Updates saved"
            logging.info("Settings updated by "+username)
            
    
    settingsform = pixel_conf.to_html_form()
    # This passes html to the template so turn off autoescaping in the template eg. |safe
    return render_template('settings.html', user=username, admin=True, form=settingsform, message=status_msg)




@app.route("/useradmin", methods=['GET', 'POST'])
def useradmin():
    global pixel_conf
    ip_address = get_ip_address()
    # Authentication first
    login_status = auth_check(ip_address)
    # not allowed even if logged in
    if login_status == "invalid":
        return redirect('/invalid')
    # Network approval not sufficient for useradmin - must be logged in
    # If not approved then issue login page
    if not (login_status == "logged_in") :
        return redirect('/login')
    # Reach here then this is logged in - also need to check they are admin
    if 'username' in session:
        username = session['username']
        if not (auth.check_admin(username)):
            # If trying to do admin, but not an admin then we log them off
            # before allowing them to login again
            session.pop('username', None)
            return render_template('login.html', message='Admin permissions required')
    # Reach here logged in as an admin user 
    user_admin = ServerUserAdmin(auth_users_filename, pixel_conf.get_value('algorithm'))
    
    # status_msg used in case we need to tell the user something
    status_msg = ""

    # if it's a post then it's either a new or edit
    if request.method == 'POST':
        # New user - just has username - creates fields based on blank user
        if 'newuser' in request.form:
            
            # check there is a username
            if 'username' in request.form:
                # Check user doesn't already exist
                requested_username = request.form['username']
                # check for minimum chars and only alphanumeric
                check_user = user_admin.validate_user(requested_username)
            else:
                check_user = (False, "Missing username or username is blank")
            if check_user[0] == False:
                return render_template('edituser.html', user=username, admin=True, form=user_admin.html_new_user(), message=check_user[1])
                
            if user_admin.user_exists (requested_username):
                return render_template('edituser.html', user=username, admin=True, form=user_admin.html_new_user(), message="User already exists, please try another username")
            else:
                # could be stage 1 (just username) or stage 2 (with password)
                # stage 1
                if request.form['newuser']=="newuser" :
                    # Create form with just username and password (then edit full details later)
                    edit_form = user_admin.html_new_user_stage2(requested_username)
                    return render_template('edituser.html',  user=username, admin=True, form=edit_form)
                # New user stage 2 - adds password
                elif request.form['newuser']=="userpassword":
                    # Already checked user so check password
                    # Check password and repeat are the same
                    # Use try except in case missing field or similar
                    try:
                        if request.form['password'] == request.form['password2']:
                            # ignore password2 as it's identical to password
                            requested_password = request.form['password']
                            check_password = user_admin.validate_password(requested_password)
                        else: 
                            # Ideally catch this using JavaScript first, but don't rely on javascript
                            check_password = (False, "Passwords do not match")
                    except:
                        check_password [False, "Invalid passwords"]
                    # If check password is false then invalid - retry password entry
                    if (check_password[0] == False):
                        edit_form = user_admin.html_new_user_stage2(requested_username)
                        return render_template('edituser.html', user=username, admin=True, form=edit_form, message=check_password[1])
                    # save username and password (rest of fields empty)
                    user_admin.add_user(requested_username, requested_password)
                    user_admin.save_users()
                    # Now load user in edit mode
                    edit_form = user_admin.html_edit_user (requested_username)
                    return render_template('edituser.html', user=username, admin=True, form=edit_form)
                        
        # Save changes                
        if 'edituser' in request.form:
            # check the user exists
            try:
                current_user = request.form['currentusername']
                if not user_admin.user_exists(current_user):
                    return redirect('useradmin?msg=Invalid update request')
            except:
                return redirect('useradmin?msg=Invalid update request')
            # current_user exists
            ## validate each value and save in temporary dictionary
            new_values = parse_form (user_admin, request.form)
            
            if 'error' in new_values.keys():
                return redirect('useradmin?msg='+new_values['error'])
                
            # If username in validated form data (then change username)
            # First check username won't be duplicate
            if 'username' in new_values and user_admin.user_exists(new_values['username']):
                return render_template('edituser.html', user=username, admin=True, form=user_admin.html_new_user(), message="User already exists")
                
            # Update all values 
            result = user_admin.update_user (current_user, new_values)
            # save 
            if result == True:
                user_admin.save_users()
                # redirect to main page
                return redirect('useradmin?msg=User updated')
            # if not then error - so reload original config
            else:
                user_admin.reload_users()
                # Gives unknown error - but should really be caught already
                return redirect('useradmin?msg=Unknown error')
            
        else:
            return redirect('useradmin?msg=Invalid update request')
    else:
        #Here add handling of password
        pass 
        # here add error message

    # if it's GET action=edit then load that user
    if request.method == "GET":
        if 'action' in request.args.keys() and 'user' in request.args.keys():
            requested_action = request.args.get('action')
            requested_user = request.args.get('user')
            # variables beginning with requested have not been validated so only use for comparisons - or perform other security checks
            if requested_action == "edit":
                # get user edit form
                html_form = user_admin.html_edit_user(requested_user)
                return render_template('edituser.html', user=username, admin=True, form=html_form)
            elif requested_action == "delete":
                # check requested_user exists
                if not user_admin.user_exists(requested_user):
                    return redirect('useradmin?msg=Invalid user')
                return render_template('deleteuser.html', user=username, admin=True, deluser=requested_user)
            # After confirmation of deletion
            elif requested_action == "delete-yes":
                # check it's a valid user first and that we are not deleting the last user
                if user_admin.user_exists(requested_user):
                    if user_admin.num_users() < 2:
                        return redirect('useradmin?msg=Cannot delete last user')
                    user_admin.delete_user(requested_user)
                    user_admin.save_users()
                    user_table = user_admin.html_table_all()
                    return render_template ('useradmin.html', user=username, admin=True, table=user_table)
            else:
                # invalid request
                return redirect('useradmin?msg=Invalid request')

        # If there is an action on the get, but not user (can only be used for new)
        elif 'action' in request.args.keys() and not 'user' in request.args.keys():
            if request.args.get('action') == "new":
                return render_template('edituser.html', user=username, admin=True, form=user_admin.html_new_user())
            else:
                # invalid request
                return redirect('useradmin?msg=Invalid request')
                
    # Reach here then show users       
        

    # display list of users
    user_table = user_admin.html_table_all()

    return render_template ('useradmin.html', user=username, admin=True, table=user_table)
        

## No authentication required for generic files
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
    
@app.route("/invalid")
def invalid():
    return render_template('invalid.html')
    
# provides list of sequences - don't authenticate
@app.route("/sequences.json")
def seqJSON ():
    return (seq_list.json())
    
# set command - authentication required
# request should either be already authenticated (eg. login successful)
# or through automation (which needs to be in the authorised network list
# If not then give login webpage
@app.route("/set")
def setSeq():
    global seq_set, upd_time, on_status
    # Authentication first
    ip_address = get_ip_address()
    login_status = auth_check(ip_address)
    # not allowed even if logged in
    if login_status == "invalid":
        return render_template('invalid.html')
    # If not approved (network or logged in) then issue login page
    if not (login_status == "network" or login_status == "logged_in"):
        return render_template('login.html')
    # Reach here then this is authorized (through network or logged in)
    
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


# Gets IP address - supports proxy headers or normal network
def get_ip_address():
    # Start by setting ip address to the real address
    ip_address = request.remote_addr
    # if Nginx proxy then take real_address
    if 'CLIENT_ADDRESS' in request.headers:
        ip_address = request.headers.get('CLIENT_ADDRESS')
    return ip_address
    
    
    
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

