# +++++++++++ FLASK +++++++++++
# Flask works with a WSGI application.
# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/shalabifinance/shalabiverse-finance'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment to production
os.environ['FLASK_ENV'] = 'production'

# Import create_app from your app package
from app import create_app

# Create the application instance
application = create_app('production')
