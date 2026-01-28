import os
from flask import Flask
from flask_migrate import Migrate
from app.models import db
from app.config import config


migrate = Migrate()


def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure instance directory exists
    if config_name == 'production':
        instance_path = os.path.join(
            app.config.get('BASE_DIR', os.path.dirname(os.path.dirname(__file__))),
            'instance'
        )
        os.makedirs(instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.income import income_bp
    from app.blueprints.expenses import expenses_bp
    from app.blueprints.accounts import accounts_bp
    from app.blueprints.debts import debts_bp
    from app.blueprints.employees import employees_bp
    from app.blueprints.reports import reports_bp

    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(income_bp, url_prefix='/income')
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(accounts_bp, url_prefix='/accounts')
    app.register_blueprint(debts_bp, url_prefix='/debts')
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(reports_bp, url_prefix='/reports')

    # Register template filters
    from app.utils import format_currency, format_date_ar
    app.jinja_env.filters['currency'] = format_currency
    app.jinja_env.filters['date_ar'] = format_date_ar

    # Create database tables and initialize default data
    with app.app_context():
        db.create_all()
        init_default_data()

    return app


def init_default_data():
    """Initialize default categories and account types"""
    from app.models import AccountType, IncomeCategory, ExpenseCategory, SystemSetting

    # Check if data already exists
    if AccountType.query.first() is not None:
        return

    # Account Types
    account_types = [
        AccountType(name_ar='كاش', name_en='cash'),
        AccountType(name_ar='بنك', name_en='bank'),
        AccountType(name_ar='محفظة', name_en='wallet')
    ]
    db.session.bulk_save_objects(account_types)

    # Income Categories
    income_categories = [
        IncomeCategory(name_ar='كورس', name_en='course'),
        IncomeCategory(name_ar='خدمة', name_en='service'),
        IncomeCategory(name_ar='محتوى', name_en='content')
    ]
    db.session.bulk_save_objects(income_categories)

    # Expense Categories
    expense_categories = [
        ExpenseCategory(name_ar='رواتب', name_en='salaries'),
        ExpenseCategory(name_ar='أدوات', name_en='tools'),
        ExpenseCategory(name_ar='تسويق', name_en='marketing'),
        ExpenseCategory(name_ar='تشغيل', name_en='operations'),
        ExpenseCategory(name_ar='أخرى', name_en='other')
    ]
    db.session.bulk_save_objects(expense_categories)

    # System Settings
    settings = [
        SystemSetting(setting_key='debt_warning_days', setting_value='7',
                     description='عدد الأيام للتنبيه قبل موعد استحقاق الدين'),
        SystemSetting(setting_key='currency', setting_value='EGP',
                     description='العملة الافتراضية')
    ]
    db.session.bulk_save_objects(settings)

    db.session.commit()
