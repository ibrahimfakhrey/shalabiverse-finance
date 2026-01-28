from flask import render_template, request, redirect, url_for, session
from datetime import date
from app.blueprints.main import main_bp
from app.models import Account, Project
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
    """Project-specific dashboard (old dashboard with project filter)"""
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
                         today=date.today())


@main_bp.route('/dashboard')
def dashboard():
    """Legacy route - redirect to project selection or last selected project"""
    selected_project_id = session.get('selected_project_id')

    if selected_project_id:
        return redirect(url_for('main.project_dashboard',
                              project_id=selected_project_id))

    return redirect(url_for('main.index'))
