from flask import Blueprint

loans_bp = Blueprint('loans', __name__)

from app.blueprints.loans import routes
