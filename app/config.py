import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, '..', 'instance', 'shalabi_verse.db')

    # Arabic/RTL Settings
    BABEL_DEFAULT_LOCALE = 'ar'
    BABEL_DEFAULT_TIMEZONE = 'Africa/Cairo'

    # Pagination
    ITEMS_PER_PAGE = 20

    # Debt notification settings
    DEBT_WARNING_DAYS = 7  # Warn 7 days before due date

    # Date formats
    DATE_FORMAT = '%Y-%m-%d'
    DISPLAY_DATE_FORMAT = '%d/%m/%Y'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration for PythonAnywhere"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

    # Override with PythonAnywhere database path
    BASE_DIR = '/home/yourusername/abdelhamed'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'shalabi_verse.db')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
