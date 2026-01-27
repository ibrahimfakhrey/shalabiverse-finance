from flask import Blueprint

employees_bp = Blueprint('employees', __name__)

from app.blueprints.employees import routes
