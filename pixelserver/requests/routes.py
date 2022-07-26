import time
from flask import request
from flask import render_template
from flask import session
from flask import redirect
from flask import Markup
import threading
import logging, os
import pixelserver
from pixelserver.statusmsg import StatusMsg
from pixelserver.serverauth import ServerAuth
from pixelserver.serveruseradmin import ServerUserAdmin

from . import requests_blueprint

@requests_blueprint.route("/")
@requests_blueprint.route("/home")
def main():
    ip_address = get_ip_address()
    login_status = pixelserver.auth.auth_check(ip_address, session)
    # not allowed even if logged in
    if login_status == "invalid":
        return redirect('/invalid')
    elif login_status == "network":
        #return ('index.html')
        return render_template('index.html', user="guest", admin=False)
    elif login_status == "logged_in":
        # Also check if admin - to show settings button
        username = session['username']
        if (pixelserver.auth.check_admin(username)):
            admin = True
        else:
            admin = False
        return render_template('index.html', user=session['username'], admin=admin)
    else:   # login required
        return redirect('/login')

@requests_blueprint.route("/login", methods=['GET', 'POST'])
def login():
    # Start by setting ip address to the real address
    ip_address = get_ip_address()
    login_status = pixelserver.auth.auth_check(ip_address, session)
    # check not an unauthorised network
    if login_status == "invalid":
        return redirect('/invalid')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (pixelserver.auth.login_user(username, password, ip_address) == True):
            # create session
            session['username'] = username
            return redirect('/')
        return render_template('login.html', message='Invalid login attempt')
    # New visit to login page
    return render_template('login.html')
    
@requests_blueprint.route("/logout")
def logout():
    if 'username' in session:
        username = session['username']
        logging.info("User logged out "+username)
    # pop off the session even if not logged in
    session.pop('username', None)
    return render_template('login.html', message="Logged out")
    
# admin and settings only available to logged in users regardless of 
# network status
@requests_blueprint.route("/settings", methods=['GET', 'POST'])
def settings():
    authorized = pixelserver.auth.check_permission_admin (get_ip_address(), session)
    if authorized != 'admin':
        if (authorized == "invalid"):
            # not allowed even if logged in
            return redirect('/invalid')
        # needs to login
        if (authorized == "login"):
            return redirect('/login')
        # Last option is "notadmin"
        # If trying to do admin, but not an admin then we log them off
        # before allowing them to login again
        session.pop('username', None)
        return render_template('login.html', message='Admin permissions required')
    
    # Reach here logged in as an admin user - update settings and/or display setting options
    username = session['username']
    status_msg = ""
    
    if request.method == 'POST':
        
        update_dict = {}
        
        # process the form - validate all parameters
        # Read into separate values to validate all before updating
        for key, value in request.form.items():
            # skip csrf token
            if key == "csrf_token":
                continue
            (status, temp_value) = pixelserver.pixel_conf.validate_parameter(key, value)
            # If we get an error at any point - don't save and go back to 
            # showing current status
            if (status == False):
                status_msg = temp_value
                break
            # Save this for updating values - use returned value
            # in case it's been sanitised (only certain types are)
            update_dict[key] = temp_value
            
        # special case any checkboxes are only included if checked
        if not ("ledinvert" in request.form.keys()):
            update_dict["ledinvert"] = False
            
                
        # As long as no error save
        if (status_msg == ""):
            for key,value in update_dict.items():
                if (pixelserver.pixel_conf.update_parameter(key, value) == False): 
                    status_msg = "Error updating settings"
                    logging.info("Error updating settings by "+username)
                    
        # Check no error and if so then save
        if not pixelserver.pixel_conf.save_settings():
            status_msg = "Error saving custom config file"
            logging.info("Error saving custom config file")
            
                    
        # As long as still no error then report success
        if (status_msg == ""):
            status_msg = "Updates saved"
            logging.info("Settings updated by "+username)
            
    
    settingsform = pixelserver.pixel_conf.to_html_form()
    # This passes html to the template so turn off autoescaping in the template eg. |safe
    return render_template('settings.html', user=username, admin=True, form=settingsform, message=status_msg)


# profile - can view own profile and change password etc
@requests_blueprint.route("/profile", methods=['GET', 'POST'])
def profile():
    ip_address = get_ip_address()
    # Status msg for feedback to user
    status_msg = ""
    # Authentication first
    login_status = pixelserver.auth.auth_check(ip_address, session)
    # not allowed even if logged in
    if login_status == "invalid":
        return redirect('/invalid')
    # Network approval not sufficient for profile - must be logged in
    # If not approved then issue login page
    if not (login_status == "logged_in") :
        return redirect('/login')
    # Reach here then this is logged in
    username = session['username']
    #get any messages
    status_msg = ""
    if 'msg' in request.args.keys():
        status_msg = request.args['msg']
        # Todo - validate
    # Create user_admin object as needed shortly
    user_admin = ServerUserAdmin(pixelserver.auth_users_filename, pixelserver.pixel_conf.get_value('algorithm'))
    # get admin to determine if settings menu is displayed
    is_admin = pixelserver.auth.check_admin(username)
    profile_form = user_admin.html_view_profile(username)
    return render_template('profile.html', user=username, admin=is_admin, form=profile_form, message=status_msg)

@requests_blueprint.route("/password", methods=['GET', 'POST'])
def password():
    ip_address = get_ip_address()
    # Status msg for feedback to user
    status_msg = ""
    # Authentication first
    login_status = pixelserver.auth.auth_check(ip_address, session)
    # not allowed even if logged in
    if login_status == "invalid":
        return redirect('/invalid')
    # Network approval not sufficient for profile - must be logged in
    # If not approved then issue login page
    if not (login_status == "logged_in") :
        return redirect('/login')
    # Reach here then this is logged in
    username = session['username']
    # logged in and have username so allow to change password
    user_admin = ServerUserAdmin(pixelserver.auth_users_filename, pixelserver.pixel_conf.get_value('algorithm'))
    # Is user admin - check for top menu only doesn't change what can be done here
    is_admin = pixelserver.auth.check_admin(username)
    password_form = user_admin.html_change_password()
    if request.method == 'POST':
        # first check existing password
        if (not 'currentpassword' in request.form):
            return render_template('password.html', user=username, admin=is_admin, form=password_form, message="Invalid request")
        if (not user_admin.check_username_password(username, request.form['currentpassword'])):
            return render_template('password.html', user=username, admin=is_admin, form=password_form, message="Incorrect username / password")
        # Now check that repeat is same
        if (not 'newpassword' in request.form) or (not 'repeatpassword' in request.form) or request.form['newpassword'] != request.form['repeatpassword']:
            return render_template('password.html', user=username, admin=is_admin, form=password_form, message="New passwords do not match")
        new_password = request.form['newpassword']
        # check password is valid (meets rules)
        result = user_admin.validate_password(new_password)
        if result[0] != True:
            return render_template('password.html', user=username, admin=is_admin, form=password_form, message=result[1])
        # passed tests so set new password
        user_admin.change_password(username, new_password)
        user_admin.save_users()
        logging.info("Password changed by "+username)
        # redirects to profile
        return redirect('profile?msg=Password changed')
        
    else:
        return render_template('password.html', user=username, admin=is_admin, form=password_form)
    
@requests_blueprint.route("/newuser", methods=['GET', 'POST'])
def newuser():
    authorized = pixelserver.auth.check_permission_admin (get_ip_address(), session)
    if authorized != 'admin':
        if (authorized == "invalid"):
            # not allowed even if logged in
            return redirect('/invalid')
        # needs to login
        if (authorized == "login"):
            return redirect('/login')
        # Last option is "notadmin"
        # If trying to do admin, but not an admin then we log them off
        # before allowing them to login again
        session.pop('username', None)
        return render_template('login.html', message='Admin permissions required')
    ### logged in as an admin user
    # get username from session and other objects required
    username = session['username']
    user_admin = ServerUserAdmin(pixelserver.auth_users_filename, pixelserver.pixel_conf.get_value('algorithm'))
    # status_msg used in case we need to tell the user something
    status_msg = ""

    # get request initial request return blank form requesting username
    if request.method == 'GET':
             
        return render_template('newuser.html', user=username, admin=True, form=user_admin.html_new_user())
    if request.method == 'POST':
        # New user - just has username - creates fields based on blank user
        # check there is a username
        if 'username' in request.form:
            # Check user doesn't already exist
            requested_username = request.form['username']
            # check for minimum chars and only alphanumeric
            check_user = user_admin.validate_user(requested_username)
        else:
            check_user = (False, "Missing username or username is blank")
        if check_user[0] == False:
            return render_template('newuser.html', user=username, admin=True, form=user_admin.html_new_user(), message=check_user[1])
            
        if user_admin.user_exists (requested_username):
            return render_template('newuser.html', user=username, admin=True, form=user_admin.html_new_user(), message="User already exists, please try another username")
        else:
            # could be stage 1 (just username) or stage 2 (with password)
            # stage 1
            if request.form['newuser']=="newuser" :
                # Create form with just username and password (then edit full details later)
                edit_form = user_admin.html_new_user_stage2(requested_username)
                return render_template('newuser.html',  user=username, admin=True, form=edit_form)
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
                    return render_template('newuser.html', user=username, admin=True, form=edit_form, message=check_password[1])
                # save username and password (rest of fields empty)
                user_admin.add_user(requested_username, requested_password)
                user_admin.save_users()
                logging.info("New user {} added by {}".format(requested_username, username))
                # Now load user in edit mode
                edit_form = user_admin.html_edit_user (requested_username)
                return render_template('edituser.html', user=username, admin=True, form=edit_form)


    
@requests_blueprint.route("/edituser", methods=['GET', 'POST'])
def edituser():
    authorized = pixelserver.auth.check_permission_admin (get_ip_address(), session)
    if authorized != 'admin':
        if (authorized == "invalid"):
            # not allowed even if logged in
            return redirect('/invalid')
        # needs to login
        if (authorized == "login"):
            return redirect('/login')
        # Last option is "notadmin"
        # If trying to do admin, but not an admin then we log them off
        # before allowing them to login again
        session.pop('username', None)
        return render_template('login.html', message='Admin permissions required')
    ### logged in as an admin user
    # get username from session and other objects required
    username = session['username']
    user_admin = ServerUserAdmin(pixelserver.auth_users_filename, pixelserver.pixel_conf.get_value('algorithm'))
    # status_msg used in case we need to tell the user something
    status_msg = ""

    # get request initial request load validate and load user
    # create edit form
    if request.method == 'GET':
        if not 'user' in request.args.keys():
            return redirect('useradmin?msg=Invalid edit user request')
        requested_user = request.args.get('user')
        # check it's a valid user
        if not user_admin.user_exists(requested_user):
            return redirect('useradmin?msg=Invalid edit user request')
        html_form = user_admin.html_edit_user(requested_user)
        return render_template('edituser.html', user=username, admin=True, form=html_form, edituser=requested_user)
        
    # Otherwise it's a post so edit save request
    else :
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
            logging.info("User {} updated by {}".format(current_user, username))
            # redirect to main page
            return redirect('useradmin?msg=User updated')
        # if not then error - so reload original config
        else:
            user_admin.reload_users()
            # Gives unknown error - but should really be caught already
            return redirect('useradmin?msg=Unknown error')


@requests_blueprint.route("/deluser", methods=['GET'])
def deluser():
    authorized = pixelserver.auth.check_permission_admin (get_ip_address(), session)
    if authorized != 'admin':
        if (authorized == "invalid"):
            # not allowed even if logged in
            return redirect('/invalid')
        # needs to login
        if (authorized == "login"):
            return redirect('/login')
        # Last option is "notadmin"
        # If trying to do admin, but not an admin then we log them off
        # before allowing them to login again
        session.pop('username', None)
        return render_template('login.html', message='Admin permissions required')
    ### logged in as an admin user
    # get username from session and other objects required
    username = session['username']
    user_admin = ServerUserAdmin(pixelserver.auth_users_filename, pixelserver.pixel_conf.get_value('algorithm'))
    # status_msg used in case we need to tell the user something
    status_msg = ""
    
    if not 'action' in request.args.keys() or not 'user' in request.args.keys():
        return redirect('useradmin?msg=Invalid delete request')
    requested_action = request.args.get('action')
    requested_user = request.args.get('user')
    # variables beginning with requested have not been validated so only use for comparisons - or perform other security checks
    if requested_action == "delete":
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
            logging.info("User {} deleted by {}".format(requested_user, username))
            return redirect('useradmin?msg=User request')
    else:
        return redirect('useradmin?msg=Invalid user')
                
                
                
@requests_blueprint.route("/passwordadmin", methods=['GET', 'POST'])
def passwordadmin():
    authorized = pixelserver.auth.check_permission_admin (get_ip_address(), session)
    if authorized != 'admin':
        if (authorized == "invalid"):
            # not allowed even if logged in
            return redirect('/invalid')
        # needs to login
        if (authorized == "login"):
            return redirect('/login')
        # Last option is "notadmin"
        # If trying to do admin, but not an admin then we log them off
        # before allowing them to login again
        session.pop('username', None)
        return render_template('login.html', message='Admin permissions required')
    ### logged in as an admin user
    # get username from session and other objects required
    username = session['username']
    user_admin = ServerUserAdmin(pixelserver.auth_users_filename, pixelserver.pixel_conf.get_value('algorithm'))
    # status_msg used in case we need to tell the user something
    status_msg = ""
     
    # if GET then just username and create
    # form with new password
    if request.method == 'GET':
        if not 'user' in request.args.keys():
            return redirect('useradmin?msg=Invalid password admin request')
        requested_user = request.args.get('user')
        # check it's a valid user
        if not user_admin.user_exists(requested_user):
            return redirect('useradmin?msg=Invalid password admin request')
        html_form = user_admin.html_password_admin(requested_user)
        return render_template('passwordadmin.html', user=username, admin=True, form=html_form)
        
    # Otherwise it's a post so edit save request
    else :                
        try:
            requested_user = request.form['username']
            if not user_admin.user_exists(requested_user):
                return redirect('useradmin?msg=Invalid update request')
        except:
            return redirect('useradmin?msg=Invalid password request')
        # requested_user exists
 
        # Now check that repeat is same
        if (not 'newpassword' in request.form) or (not 'repeatpassword' in request.form) or request.form['newpassword'] != request.form['repeatpassword']:
            password_form = user_admin.html_password_admin(requested_user)
            return render_template('passwordadmin.html', user=username, admin=True, form=password_form, message="New passwords do not match")
        new_password = request.form['newpassword']
        # check password is valid (meets rules)
        result = user_admin.validate_password(new_password)
        if result[0] != True:
            password_form = user_admin.html_password_admin(requested_user)
            return render_template('passwordadmin.html', user=username, admin=True, form=password_form, message=result[1])
        # passed tests so set new password
        user_admin.change_password(requested_user, new_password)
        user_admin.save_users()
        logging.info("User {} password changed by {}".format(requested_user, username))
        # redirects to useradmin
        return redirect('useradmin?msg=Password changed')
                
@requests_blueprint.route("/useradmin", methods=['GET'])
def useradmin():
    authorized = pixelserver.auth.check_permission_admin (get_ip_address(), session)
    if authorized != 'admin':
        if (authorized == "invalid"):
            # not allowed even if logged in
            return redirect('/invalid')
        # needs to login
        if (authorized == "login"):
            return redirect('/login')
        # Last option is "notadmin"
        # If trying to do admin, but not an admin then we log them off
        # before allowing them to login again
        session.pop('username', None)
        return render_template('login.html', message='Admin permissions required')
    ### logged in as an admin user
    # get username from session and other objects required
    username = session['username']
    user_admin = ServerUserAdmin(pixelserver.auth_users_filename, pixelserver.pixel_conf.get_value('algorithm'))
    # status_msg used in case we need to tell the user something
    status_msg = ""
                
    # Reach here then show users       
    # display list of users
    user_table = user_admin.html_table_all()

    return render_template ('useradmin.html', user=username, admin=True, table=user_table)
    

## No authentication required for generic files
@requests_blueprint.route("/pixels.css")
def css():
    return render_template('pixels.css'), 200, {'Content-Type': 'text/css; charset=utf-8'}

@requests_blueprint.route("/pixels.js")
def js():
    return render_template('pixels.js'), 200, {'Content-Type': 'text/javascript; charset=utf-8'}
    
@requests_blueprint.route("/jquery.min.js")
def jquery():
    return render_template('jquery.min.js'), 200, {'Content-Type': 'text/javascript; charset=utf-8'}
   
@requests_blueprint.route("/jquery-ui.min.js")
def jqueryui():
    return render_template('jquery-ui.min.js'), 200, {'Content-Type': 'text/javascript; charset=utf-8'}
    
@requests_blueprint.route("/invalid")
def invalid():
    return render_template('invalid.html')
    
# provides list of sequences - don't authenticate
@requests_blueprint.route("/sequences.json")
def seqJSON ():
    return (pixelserver.seq_list.json())
    
# set command - authentication required
# request should either be already authenticated (eg. login successful)
# or through automation (which needs to be in the authorised network list
# If not then give login webpage
@requests_blueprint.route("/set")
def setSeq():
    # Authentication first
    ip_address = get_ip_address()
    login_status = pixelserver.auth.auth_check(ip_address, session)
    # not allowed even if logged in
    if login_status == "invalid":
        return render_template('invalid.html')
    # If not approved (network or logged in) then issue login page
    if not (login_status == "network" or login_status == "logged_in"):
        return render_template('login.html')
    # Reach here then this is authorized (through network or logged in)
    
    status = StatusMsg()
    status.set_server_values(pixelserver.seq_set)
    new_values = {}
    # perform first stage validation on data sent
    this_arg = request.args.get('seq', default = 'alloff', type = str)
    if (pixelserver.seq_list.validate_sequence(this_arg) == True):
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
    if (pixelserver.seq_list.validate_color_string(this_arg)):
        new_values["colors"] = this_arg
    else:
        status.set_status ("error", "Invalid colors")
        return status.get_message()
    # If reach here then it was successful for copy temp dict to actual
    pixelserver.seq_set = new_values
    
    # Check for toggle status - if on and toggle=true then turn off
    # this is done afer pixelserver.seq_set is copied - so override pixelserver.seq_set 
    this_arg = request.args.get('toggle', default = 'False', type = str)
    # only handle if toggle="True", otherwise ignore the parameter
    if (this_arg == "True" or this_arg == "true"):
        if (pixelserver.on_status == True):
            # Override request and replace with AllOff
            pixelserver.seq_set["sequence"] = "alloff" 
            pixelserver.on_status = False
        else:
            # Action as normal, but set to true
            pixelserver.on_status = True
            
    # Update successful status
    status.set_server_values(pixelserver.seq_set)
    status.set_status ("success")
        
    # update time to notify other thread it's changed
    pixelserver.upd_time = time.time()
    return status.get_message ()


# Gets IP address - supports proxy headers or normal network
def get_ip_address():
    # Start by setting ip address to the real address
    ip_address = request.remote_addr
    if 'X-Real-IP' in request.headers and pixelserver.auth.check_proxy(ip_address):
        proxy_addr = ip_address
        ip_address = request.headers.get('X-Real_IP')
        logging.info("Proxy connection {} is {}".format(proxy_addr, ip_address))
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



