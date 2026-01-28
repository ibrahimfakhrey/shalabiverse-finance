from flask import render_template, request, redirect, url_for, flash, session
from app.blueprints.reports import reports_bp
from datetime import date
from app.utils import (
    get_date_range_filter, calculate_total_income, calculate_total_expenses,
    calculate_profit_loss, calculate_equity, get_income_by_category, get_expense_by_category
)


@reports_bp.route('/profit-loss')
def profit_loss():
    """Profit & Loss statement for the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    period = request.args.get('period', 'month')
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')

    if custom_start:
        custom_start = date.fromisoformat(custom_start)
    if custom_end:
        custom_end = date.fromisoformat(custom_end)

    start_date, end_date = get_date_range_filter(period, custom_start, custom_end)

    total_income = calculate_total_income(start_date, end_date, project_id=project_id)
    total_expenses = calculate_total_expenses(start_date, end_date, project_id=project_id)
    profit_loss_val = calculate_profit_loss(start_date, end_date, project_id=project_id)

    return render_template('reports/profit_loss.html',
                         total_income=total_income,
                         total_expenses=total_expenses,
                         profit_loss=profit_loss_val,
                         start_date=start_date,
                         end_date=end_date,
                         selected_period=period)


@reports_bp.route('/income-summary')
def income_summary():
    """Income summary by category for the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    period = request.args.get('period', 'month')
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')

    if custom_start:
        custom_start = date.fromisoformat(custom_start)
    if custom_end:
        custom_end = date.fromisoformat(custom_end)

    start_date, end_date = get_date_range_filter(period, custom_start, custom_end)

    income_by_category = get_income_by_category(start_date, end_date, project_id=project_id)
    total_income = calculate_total_income(start_date, end_date, project_id=project_id)

    return render_template('reports/income_summary.html',
                         income_by_category=income_by_category,
                         total_income=total_income,
                         start_date=start_date,
                         end_date=end_date,
                         selected_period=period)


@reports_bp.route('/expense-summary')
def expense_summary():
    """Expense summary by category for the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    period = request.args.get('period', 'month')
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')

    if custom_start:
        custom_start = date.fromisoformat(custom_start)
    if custom_end:
        custom_end = date.fromisoformat(custom_end)

    start_date, end_date = get_date_range_filter(period, custom_start, custom_end)

    expense_by_category = get_expense_by_category(start_date, end_date, project_id=project_id)
    total_expenses = calculate_total_expenses(start_date, end_date, project_id=project_id)

    return render_template('reports/expense_summary.html',
                         expense_by_category=expense_by_category,
                         total_expenses=total_expenses,
                         start_date=start_date,
                         end_date=end_date,
                         selected_period=period)


@reports_bp.route('/equity')
def equity():
    """Project equity report for the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    equity_data = calculate_equity(project_id=project_id)

    return render_template('reports/equity.html', equity=equity_data)
