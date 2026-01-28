from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from app.models import db, IncomeTransaction, ExpenseTransaction, Account, Debt


def format_currency(value):
    """Format number as Arabic currency"""
    if value is None:
        return "0.00"
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return "0.00"


def format_date_ar(value):
    """Format date for Arabic display"""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d').date()
        except:
            return value

    if not isinstance(value, (date, datetime)):
        return value

    return value.strftime('%d/%m/%Y')


def get_date_range_filter(period, custom_start=None, custom_end=None):
    """
    Get date range based on period filter
    periods: 'today', 'week', 'month', 'year', 'custom'
    """
    today = date.today()

    if period == 'today':
        return today, today
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif period == 'month':
        start = today.replace(day=1)
        return start, today
    elif period == 'year':
        start = today.replace(month=1, day=1)
        return start, today
    elif period == 'custom' and custom_start and custom_end:
        return custom_start, custom_end
    else:
        # Default to current month
        start = today.replace(day=1)
        return start, today


def calculate_total_income(start_date=None, end_date=None, account_id=None, project_id=None):
    """Calculate total income for period, account, and project"""
    query = db.session.query(func.sum(IncomeTransaction.amount))

    if project_id:
        query = query.filter(IncomeTransaction.project_id == project_id)
    if start_date:
        query = query.filter(IncomeTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(IncomeTransaction.transaction_date <= end_date)
    if account_id:
        query = query.filter(IncomeTransaction.account_id == account_id)

    result = query.scalar()
    return float(result) if result else 0.0


def calculate_total_expenses(start_date=None, end_date=None, account_id=None, project_id=None):
    """Calculate total expenses for period, account, and project"""
    query = db.session.query(func.sum(ExpenseTransaction.amount))

    if project_id:
        query = query.filter(ExpenseTransaction.project_id == project_id)
    if start_date:
        query = query.filter(ExpenseTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(ExpenseTransaction.transaction_date <= end_date)
    if account_id:
        query = query.filter(ExpenseTransaction.account_id == account_id)

    result = query.scalar()
    return float(result) if result else 0.0


def calculate_profit_loss(start_date=None, end_date=None, account_id=None, project_id=None):
    """Calculate profit/loss: Income - Expenses"""
    income = calculate_total_income(start_date, end_date, account_id, project_id)
    expenses = calculate_total_expenses(start_date, end_date, account_id, project_id)
    return income - expenses


def calculate_total_balance(account_id=None, project_id=None):
    """Calculate total balance across accounts"""
    query = db.session.query(func.sum(Account.current_balance))

    if project_id:
        query = query.filter(Account.project_id == project_id)
    if account_id:
        query = query.filter(Account.id == account_id)
    else:
        query = query.filter(Account.is_active == True)

    result = query.scalar()
    return float(result) if result else 0.0


def calculate_equity(project_id=None):
    """
    Calculate project equity: Assets - Liabilities
    Assets = Total account balances + Debts owed to us (unpaid)
    Liabilities = Debts owed by us (unpaid)
    """
    # Assets: Current balances
    total_balance = calculate_total_balance(project_id=project_id)

    # Assets: Unpaid debts owed to us (لينا)
    debts_to_us_query = db.session.query(func.sum(Debt.remaining_amount))\
        .filter(Debt.debt_type == 'owed_to_us', Debt.is_paid == False)
    if project_id:
        debts_to_us_query = debts_to_us_query.filter(Debt.project_id == project_id)
    debts_to_us = debts_to_us_query.scalar() or 0

    # Liabilities: Unpaid debts owed by us (علينا)
    debts_by_us_query = db.session.query(func.sum(Debt.remaining_amount))\
        .filter(Debt.debt_type == 'owed_by_us', Debt.is_paid == False)
    if project_id:
        debts_by_us_query = debts_by_us_query.filter(Debt.project_id == project_id)
    debts_by_us = debts_by_us_query.scalar() or 0

    assets = float(total_balance) + float(debts_to_us)
    liabilities = float(debts_by_us)

    return {
        'assets': assets,
        'liabilities': liabilities,
        'equity': assets - liabilities
    }


def get_upcoming_debts(days=7, project_id=None):
    """Get debts due within specified days"""
    today = date.today()
    due_date = today + timedelta(days=days)

    query = Debt.query.filter(
        Debt.debt_type == 'owed_by_us',
        Debt.is_paid == False,
        Debt.due_date.isnot(None),
        Debt.due_date.between(today, due_date)
    )

    if project_id:
        query = query.filter(Debt.project_id == project_id)

    debts = query.order_by(Debt.due_date).all()
    return debts


def get_income_by_category(start_date=None, end_date=None, project_id=None):
    """Get income grouped by category"""
    from app.models import IncomeCategory

    query = db.session.query(
        IncomeCategory.name_ar,
        func.sum(IncomeTransaction.amount).label('total')
    ).join(IncomeTransaction).group_by(IncomeCategory.id)

    if project_id:
        query = query.filter(IncomeTransaction.project_id == project_id)
    if start_date:
        query = query.filter(IncomeTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(IncomeTransaction.transaction_date <= end_date)

    return query.all()


def get_expense_by_category(start_date=None, end_date=None, project_id=None):
    """Get expenses grouped by category"""
    from app.models import ExpenseCategory

    query = db.session.query(
        ExpenseCategory.name_ar,
        func.sum(ExpenseTransaction.amount).label('total')
    ).join(ExpenseTransaction).group_by(ExpenseCategory.id)

    if project_id:
        query = query.filter(ExpenseTransaction.project_id == project_id)
    if start_date:
        query = query.filter(ExpenseTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(ExpenseTransaction.transaction_date <= end_date)

    return query.all()


def get_project_summary(project_id):
    """Get comprehensive financial summary for a project"""
    from app.models import Employee

    # Calculate total balance for project
    total_balance = calculate_total_balance(project_id=project_id)

    # Count active employees
    employee_count = Employee.query.filter_by(
        project_id=project_id,
        is_active=True
    ).count()

    # Calculate debts
    debts_to_us_query = db.session.query(func.sum(Debt.remaining_amount))\
        .filter(Debt.project_id == project_id,
                Debt.debt_type == 'owed_to_us',
                Debt.is_paid == False)
    debts_to_us = debts_to_us_query.scalar() or 0

    debts_by_us_query = db.session.query(func.sum(Debt.remaining_amount))\
        .filter(Debt.project_id == project_id,
                Debt.debt_type == 'owed_by_us',
                Debt.is_paid == False)
    debts_by_us = debts_by_us_query.scalar() or 0

    # Count active accounts
    account_count = Account.query.filter_by(
        project_id=project_id,
        is_active=True
    ).count()

    return {
        'total_balance': float(total_balance),
        'employee_count': employee_count,
        'debts_to_us': float(debts_to_us),
        'debts_by_us': float(debts_by_us),
        'account_count': account_count
    }
