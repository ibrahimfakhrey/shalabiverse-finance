import sys
import os

# Add project directory to Python path
project_home = '/home/yourusername/abdelhamed'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment to production
os.environ['FLASK_ENV'] = 'production'

from app import create_app

# Create application instance
application = create_app('production')
