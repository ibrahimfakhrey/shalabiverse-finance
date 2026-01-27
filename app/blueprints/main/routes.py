from flask import render_template, request
from datetime import date
from app.blueprints.main import main_bp
from app.models import Account
from app.utils import (
    get_date_range_filter, calculate_total_income, calculate_total_expenses,
    calculate_profit_loss, calculate_total_balance, get_upcoming_debts
)


@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """Main dashboard with key metrics and filters"""

    # Get filter parameters
    period = request.args.get('period', 'month')
    account_id = request.args.get('account_id', type=int)
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')

    # Parse custom dates if provided
    if custom_start:
        custom_start = date.fromisoformat(custom_start)
    if custom_end:
        custom_end = date.fromisoformat(custom_end)

    # Get date range
    start_date, end_date = get_date_range_filter(period, custom_start, custom_end)

    # Calculate key metrics
    total_balance = calculate_total_balance(account_id)
    total_income = calculate_total_income(start_date, end_date, account_id)
    total_expenses = calculate_total_expenses(start_date, end_date, account_id)
    profit_loss = calculate_profit_loss(start_date, end_date, account_id)

    # Get upcoming debts (7 days warning)
    upcoming_debts = get_upcoming_debts(days=7)

    # Get accounts for filter
    accounts = Account.query.filter_by(is_active=True).all()

    return render_template('main/dashboard.html',
                         total_balance=total_balance,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         profit_loss=profit_loss,
                         upcoming_debts=upcoming_debts,
                         accounts=accounts,
                         selected_period=period,
                         selected_account=account_id,
                         start_date=start_date,
                         end_date=end_date,
                         today=date.today())
