from flask import render_template, request, redirect, url_for, session
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from app.blueprints.main import main_bp
from app.models import (
    db, Account, Project, Loan, LoanPayment, ExpenseTransaction, IncomeTransaction
)
from app.utils import (
    get_date_range_filter, calculate_total_income, calculate_total_expenses,
    calculate_profit_loss, calculate_total_balance, get_upcoming_debts,
    get_project_summary
)


@main_bp.route('/')
def index():
    """Landing page - show all projects as cards"""
    projects = Project.query.filter_by(is_active=True)\
        .order_by(Project.created_at.desc()).all()

    # Get summary for each project
    project_data = []
    for project in projects:
        summary = get_project_summary(project.id)
        project_data.append({
            'project': project,
            'summary': summary
        })

    return render_template('main/projects_overview.html',
                         project_data=project_data)


@main_bp.route('/project/<int:project_id>/dashboard')
def project_dashboard(project_id):
    """Project-specific dashboard with KPIs, loans, and cost breakdown"""
    project = Project.query.get_or_404(project_id)

    # Store in session for navigation
    session['selected_project_id'] = project_id
    session['selected_project_name'] = project.name_ar

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

    # Calculate key metrics (now filtered by project)
    total_balance = calculate_total_balance(account_id, project_id=project_id)
    total_income = calculate_total_income(start_date, end_date, account_id, project_id=project_id)
    total_expenses = calculate_total_expenses(start_date, end_date, account_id, project_id=project_id)
    profit_loss = calculate_profit_loss(start_date, end_date, account_id, project_id=project_id)

    # Get upcoming debts for this project
    upcoming_debts = get_upcoming_debts(days=7, project_id=project_id)

    # Get accounts for this project only
    accounts = Account.query.filter_by(
        project_id=project_id,
        is_active=True
    ).all()

    # === BUILD vs OPERATING COSTS (for the selected period) ===
    build_costs_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'building',
        ExpenseTransaction.transaction_date >= start_date,
        ExpenseTransaction.transaction_date <= end_date
    )
    build_costs = float(build_costs_query.scalar() or 0)

    operating_costs_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating',
        ExpenseTransaction.transaction_date >= start_date,
        ExpenseTransaction.transaction_date <= end_date
    )
    operating_costs = float(operating_costs_query.scalar() or 0)

    # === LOAN SUMMARY ===
    total_loan_debt_query = db.session.query(func.sum(Loan.remaining_amount)).filter(
        Loan.project_id == project_id,
        Loan.is_paid == False
    )
    total_loan_debt = float(total_loan_debt_query.scalar() or 0)

    # Upcoming loan payments (loans due within 30 days)
    upcoming_loans = Loan.query.filter(
        Loan.project_id == project_id,
        Loan.is_paid == False,
        Loan.due_date.isnot(None),
        Loan.due_date <= date.today() + relativedelta(days=30),
        Loan.due_date >= date.today()
    ).order_by(Loan.due_date).all()

    # Overdue loans
    overdue_loans = Loan.query.filter(
        Loan.project_id == project_id,
        Loan.is_paid == False,
        Loan.due_date.isnot(None),
        Loan.due_date < date.today()
    ).all()

    active_loans_count = Loan.query.filter_by(
        project_id=project_id, is_paid=False
    ).count()

    # === KPIs ===
    today = date.today()
    six_months_ago = today - relativedelta(months=6)

    # Burn Rate (avg monthly operating expenses, last 6 months)
    recent_expenses_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating',
        ExpenseTransaction.transaction_date >= six_months_ago,
        ExpenseTransaction.transaction_date <= today
    )
    recent_expenses = float(recent_expenses_query.scalar() or 0)

    months_query = db.session.query(
        func.distinct(func.strftime('%Y-%m', ExpenseTransaction.transaction_date))
    ).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating',
        ExpenseTransaction.transaction_date >= six_months_ago,
        ExpenseTransaction.transaction_date <= today
    )
    months_with_data = months_query.count() or 1
    burn_rate = recent_expenses / months_with_data

    # Runway
    runway_months = (total_balance / burn_rate) if burn_rate > 0 else float('inf')

    # Gross Margin (all time)
    all_income = calculate_total_income(project_id=project_id)
    direct_costs_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating',
        ExpenseTransaction.is_direct_cost == True
    )
    direct_costs = float(direct_costs_query.scalar() or 0)
    gross_profit = all_income - direct_costs
    gross_margin_pct = (gross_profit / all_income * 100) if all_income > 0 else 0

    return render_template('main/dashboard.html',
                         project=project,
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
                         today=date.today(),
                         # Build vs Operating
                         build_costs=build_costs,
                         operating_costs=operating_costs,
                         # Loan summary
                         total_loan_debt=total_loan_debt,
                         upcoming_loans=upcoming_loans,
                         overdue_loans=overdue_loans,
                         active_loans_count=active_loans_count,
                         # KPIs
                         burn_rate=burn_rate,
                         runway_months=runway_months,
                         gross_margin_pct=gross_margin_pct)


@main_bp.route('/dashboard')
def dashboard():
    """Legacy route - redirect to project selection or last selected project"""
    selected_project_id = session.get('selected_project_id')

    if selected_project_id:
        return redirect(url_for('main.project_dashboard',
                              project_id=selected_project_id))

    return redirect(url_for('main.index'))
