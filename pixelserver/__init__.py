import pixelserver
from pixelserver.pixelconfig import PixelConfig
from pixelserver.pixelseq import PixelSeq, SeqList
from pixelserver.serverauth import ServerAuth
from flask import Flask
from flask_wtf.csrf import CSRFProtect
import random
import string
import time
import logging, os


# Globals for passing information between threads
# needs default settings
upd_time = time.time()
seq_set = {
    "sequence" : "alloff",
    "delay" : 900,
    "reverse" : 0,
    "colors" : "ffffff"
    }
pixel_conf = None
# used for toggle option
# Ignored unless toggle=True parameter
on_status = False

# List of sequences
seq_list = SeqList()



def load_config(default_config_filename, custom_config_filename, custom_light_config_filename):
    return PixelConfig(default_config_filename, custom_config_filename, custom_light_config_filename)

# Should always run with csrf=True
# csrf_enable=False is only included for testing purposes (disables CSRF)
def create_app(auth_config_filename, auth_users_filename, log_filename, csrf_enable=True):
    pixelserver.auth_config_filename = auth_config_filename
    pixelserver.auth_users_filename = auth_users_filename
    
    start_logging (log_filename)
    pixelserver.auth = ServerAuth(auth_config_filename, auth_users_filename)
    
    if csrf_enable:
        csrf = CSRFProtect()
    app = Flask(
        __name__,
        template_folder="www"
        )
    # Create a secret_key to last whilst the program is running
    app.secret_key = ''.join(random.choice(string.ascii_letters) for i in range(15))
    if csrf_enable:
        csrf.init_app(app)
    register_blueprints(app)
    return app
    
#Turn on logging through systemd
def start_logging(log_filename):
    logging.basicConfig(level=logging.INFO, filename=log_filename, filemode='a', format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info ("PixelServer application start")
    
#Register routes as @requests
def register_blueprints(app):
    from pixelserver.requests import requests_blueprint
    app.register_blueprint(requests_blueprint)