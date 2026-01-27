from flask import Blueprint

debts_bp = Blueprint('debts', __name__)

from app.blueprints.debts import routes
