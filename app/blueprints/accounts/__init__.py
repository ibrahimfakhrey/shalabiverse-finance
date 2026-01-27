from flask import Blueprint

accounts_bp = Blueprint('accounts', __name__)

from app.blueprints.accounts import routes
