from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200))
    pin_hash = db.Column(db.String(256), nullable=True)  # Hashed PIN for project access
    phase = db.Column(db.String(20), default='building')  # 'building' or 'operating'
    owner_capital = db.Column(db.Numeric(15, 2), default=0.00)  # Initial investment/capital
    is_active = db.Column(db.Boolean, default=True)

    def set_pin(self, pin):
        """Hash and store the PIN"""
        self.pin_hash = generate_password_hash(str(pin), method='pbkdf2:sha256')

    def check_pin(self, pin):
        """Verify PIN against stored hash"""
        if not self.pin_hash:
            return False
        return check_password_hash(self.pin_hash, str(pin))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    accounts = db.relationship('Account', backref='project', lazy='dynamic')
    employees = db.relationship('Employee', backref='project', lazy='dynamic')
    debts = db.relationship('Debt', backref='project', lazy='dynamic')
    income_transactions = db.relationship('IncomeTransaction', backref='project', lazy='dynamic')
    expense_transactions = db.relationship('ExpenseTransaction', backref='project', lazy='dynamic')
    loans = db.relationship('Loan', backref='project', lazy='dynamic')


class AccountType(db.Model):
    __tablename__ = 'account_types'

    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(50), nullable=False)
    name_en = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    accounts = db.relationship('Account', backref='account_type', lazy='dynamic')


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    account_type_id = db.Column(db.Integer, db.ForeignKey('account_types.id'), nullable=False)
    initial_balance = db.Column(db.Numeric(15, 2), default=0.00)
    current_balance = db.Column(db.Numeric(15, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    income_transactions = db.relationship('IncomeTransaction', backref='account', lazy='dynamic')
    expense_transactions = db.relationship('ExpenseTransaction', backref='account', lazy='dynamic')

    def update_balance(self):
        """Recalculate current balance based on initial balance, transactions, loans, and loan payments"""
        total_income = db.session.query(func.sum(IncomeTransaction.amount))\
            .filter(IncomeTransaction.account_id == self.id).scalar() or 0
        total_expenses = db.session.query(func.sum(ExpenseTransaction.amount))\
            .filter(ExpenseTransaction.account_id == self.id).scalar() or 0

        # Loans received into this account (cash IN)
        total_loans = db.session.query(func.sum(Loan.amount))\
            .filter(Loan.account_id == self.id).scalar() or 0

        # Loan payments from this account (cash OUT)
        total_loan_payments = db.session.query(func.sum(LoanPayment.amount))\
            .filter(LoanPayment.account_id == self.id).scalar() or 0

        # Debts owed BY us = someone gave us money (cash IN)
        total_debts_by_us = db.session.query(func.sum(Debt.original_amount))\
            .filter(Debt.account_id == self.id, Debt.debt_type == 'owed_by_us').scalar() or 0

        # Debts owed TO us = we gave someone money (cash OUT)
        total_debts_to_us = db.session.query(func.sum(Debt.original_amount))\
            .filter(Debt.account_id == self.id, Debt.debt_type == 'owed_to_us').scalar() or 0

        # Debt payments on debts BY us = we pay back (cash OUT)
        debt_payments_by_us = db.session.query(func.sum(DebtPayment.amount))\
            .join(Debt).filter(
                DebtPayment.account_id == self.id,
                Debt.debt_type == 'owed_by_us'
            ).scalar() or 0

        # Debt payments on debts TO us = they pay us back (cash IN)
        debt_payments_to_us = db.session.query(func.sum(DebtPayment.amount))\
            .join(Debt).filter(
                DebtPayment.account_id == self.id,
                Debt.debt_type == 'owed_to_us'
            ).scalar() or 0

        self.current_balance = (float(self.initial_balance) 
                                + float(total_income) 
                                - float(total_expenses)
                                + float(total_loans)
                                - float(total_loan_payments)
                                + float(total_debts_by_us)
                                - float(total_debts_to_us)
                                - float(debt_payments_by_us)
                                + float(debt_payments_to_us))
        db.session.commit()


class IncomeCategory(db.Model):
    __tablename__ = 'income_categories'

    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('IncomeTransaction', backref='category', lazy='dynamic')


class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'

    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('ExpenseTransaction', backref='category', lazy='dynamic')


class IncomeTransaction(db.Model):
    __tablename__ = 'income_transactions'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('income_categories.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False, default=date.today)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExpenseTransaction(db.Model):
    __tablename__ = 'expense_transactions'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False, default=date.today)
    phase = db.Column(db.String(20), default='operating')  # 'building' or 'operating'
    notes = db.Column(db.Text)
    is_salary = db.Column(db.Boolean, default=False)
    is_direct_cost = db.Column(db.Boolean, default=False)  # Direct cost vs operating expense
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    base_salary = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    contract_type = db.Column(db.String(20), default='full-time')  # full-time/part-time/freelancer
    hire_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    salary_payments = db.relationship('SalaryPayment', backref='employee', lazy='dynamic')
    expense_transactions = db.relationship('ExpenseTransaction', backref='employee', lazy='dynamic')


class SalaryPayment(db.Model):
    __tablename__ = 'salary_payments'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    base_salary = db.Column(db.Numeric(15, 2), nullable=False)
    deductions = db.Column(db.Numeric(15, 2), default=0.00)
    bonus = db.Column(db.Numeric(15, 2), default=0.00)
    commission = db.Column(db.Numeric(15, 2), default=0.00)
    net_salary = db.Column(db.Numeric(15, 2), nullable=False)
    expense_transaction_id = db.Column(db.Integer, db.ForeignKey('expense_transactions.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    expense_transaction = db.relationship('ExpenseTransaction', foreign_keys=[expense_transaction_id])

    def calculate_net_salary(self):
        """Calculate net salary: base - deductions + bonus + commission"""
        self.net_salary = float(self.base_salary) - float(self.deductions or 0) + \
                         float(self.bonus or 0) + float(self.commission or 0)


class Debt(db.Model):
    __tablename__ = 'debts'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    debt_type = db.Column(db.String(20), nullable=False)  # 'owed_to_us' or 'owed_by_us'
    person_name = db.Column(db.String(200), nullable=False)
    original_amount = db.Column(db.Numeric(15, 2), nullable=False)
    remaining_amount = db.Column(db.Numeric(15, 2), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))  # Account linked to debt
    due_date = db.Column(db.Date)
    is_paid = db.Column(db.Boolean, default=False)
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, partial, paid
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payments = db.relationship('DebtPayment', backref='debt', lazy='dynamic', cascade='all, delete-orphan')

    def is_upcoming(self, days=7):
        """Check if debt is due within specified days"""
        if not self.due_date or self.is_paid:
            return False
        days_until_due = (self.due_date - date.today()).days
        return 0 <= days_until_due <= days

    def is_overdue(self):
        """Check if debt is overdue"""
        if not self.due_date or self.is_paid:
            return False
        return self.due_date < date.today()

    def update_status(self):
        """Update payment status based on remaining amount"""
        if float(self.remaining_amount) <= 0:
            self.payment_status = 'paid'
            self.is_paid = True
        elif float(self.remaining_amount) < float(self.original_amount):
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'


class DebtPayment(db.Model):
    __tablename__ = 'debt_payments'

    id = db.Column(db.Integer, primary_key=True)
    debt_id = db.Column(db.Integer, db.ForeignKey('debts.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship('Account')


class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    lender_name = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    received_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date)
    interest_rate = db.Column(db.Numeric(5, 2), default=0.00)
    remaining_amount = db.Column(db.Numeric(15, 2), nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payments = db.relationship('LoanPayment', backref='loan', lazy='dynamic', cascade='all, delete-orphan')
    account = db.relationship('Account', foreign_keys=[account_id])

    def is_upcoming(self, days=7):
        """Check if loan is due within specified days"""
        if not self.due_date or self.is_paid:
            return False
        days_until_due = (self.due_date - date.today()).days
        return 0 <= days_until_due <= days

    def is_overdue(self):
        """Check if loan is overdue"""
        if not self.due_date or self.is_paid:
            return False
        return self.due_date < date.today()

    def update_status(self):
        """Update paid status based on remaining amount"""
        if float(self.remaining_amount) <= 0:
            self.is_paid = True
            self.remaining_amount = 0


class LoanPayment(db.Model):
    __tablename__ = 'loan_payments'

    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship('Account', foreign_keys=[account_id])


class SystemSetting(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
