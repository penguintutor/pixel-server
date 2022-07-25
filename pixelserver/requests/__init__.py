"""
The recipes Blueprint creates routes for this application
"""
from flask import Blueprint
requests_blueprint = Blueprint('requests', __name__, template_folder='../www')

from . import routes
