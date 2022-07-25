import pixelserver.pixelapp
from pixelserver.pixelconfig import PixelConfig
from pixelserver.pixelseq import PixelSeq, SeqList
from pixelserver.statusmsg import StatusMsg
from pixelserver.customlight import CustomLight
from pixelserver.serverauth import ServerAuth
from pixelserver.serveruseradmin import ServerUserAdmin
from pixelserver.serveruser import ServerUser
from flask import Flask
from flask_wtf.csrf import CSRFProtect
import random
import string
import time
import logging, os

auth_config_filename = "auth.cfg"
auth_users_filename = "users.cfg"
log_filename = "/var/log/pixelserver.log"

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

# Turn on logging through systemd
logging.basicConfig(level=logging.INFO, filename=log_filename, filemode='a', format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.info ("PixelServer application start")


auth = ServerAuth(auth_config_filename, auth_users_filename)

def load_config(default_config_filename, custom_config_filename, custom_light_config_filename):
    return PixelConfig(default_config_filename, custom_config_filename, custom_light_config_filename)

def create_app(config_file=None):
    csrf = CSRFProtect()
    app = Flask(
        __name__,
        template_folder="www"
        )
    # Create a secret_key to last whilst the program is running
    app.secret_key = ''.join(random.choice(string.ascii_letters) for i in range(15))
    csrf.init_app(app)
    register_blueprints(app)
    return app
    
def register_blueprints(app):
    from pixelserver.requests import requests_blueprint
    app.register_blueprint(requests_blueprint)