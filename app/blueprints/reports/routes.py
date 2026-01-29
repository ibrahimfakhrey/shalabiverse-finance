from flask import render_template, request, redirect, url_for, flash, session
from app.blueprints.reports import reports_bp
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from app.models import (
    db, Project, IncomeTransaction, ExpenseTransaction, Account,
    Loan, LoanPayment, Debt
)
from app.utils import (
    get_date_range_filter, calculate_total_income, calculate_total_expenses,
    calculate_profit_loss, calculate_equity, get_income_by_category, get_expense_by_category,
    calculate_total_balance
)


def _get_project_id():
    """Helper to get selected project id from session"""
    project_id = session.get('selected_project_id')
    if not project_id:
        return None
    return project_id


@reports_bp.route('/profit-loss')
def profit_loss():
    """Enhanced Profit & Loss statement - excludes building phase expenses and loans"""
    project_id = _get_project_id()
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

    # Operating Revenue (all income)
    total_income = calculate_total_income(start_date, end_date, project_id=project_id)

    # Direct Costs (operating phase, is_direct_cost=True)
    direct_costs_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating',
        ExpenseTransaction.is_direct_cost == True,
        ExpenseTransaction.transaction_date >= start_date,
        ExpenseTransaction.transaction_date <= end_date
    )
    direct_costs = float(direct_costs_query.scalar() or 0)

    # Gross Profit
    gross_profit = total_income - direct_costs
    gross_margin_pct = (gross_profit / total_income * 100) if total_income > 0 else 0

    # Operating Expenses (operating phase, NOT direct cost)
    operating_expenses_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating',
        ExpenseTransaction.is_direct_cost == False,
        ExpenseTransaction.transaction_date >= start_date,
        ExpenseTransaction.transaction_date <= end_date
    )
    operating_expenses = float(operating_expenses_query.scalar() or 0)

    # Net Profit (Operating Revenue - Direct Costs - Operating Expenses)
    net_profit = gross_profit - operating_expenses
    net_margin_pct = (net_profit / total_income * 100) if total_income > 0 else 0

    # Building phase expenses (shown as info, NOT included in P&L)
    building_expenses_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'building',
        ExpenseTransaction.transaction_date >= start_date,
        ExpenseTransaction.transaction_date <= end_date
    )
    building_expenses = float(building_expenses_query.scalar() or 0)

    # Income by category
    income_by_category = get_income_by_category(start_date, end_date, project_id=project_id)

    return render_template('reports/profit_loss.html',
                         total_income=total_income,
                         direct_costs=direct_costs,
                         gross_profit=gross_profit,
                         gross_margin_pct=gross_margin_pct,
                         operating_expenses=operating_expenses,
                         net_profit=net_profit,
                         net_margin_pct=net_margin_pct,
                         building_expenses=building_expenses,
                         income_by_category=income_by_category,
                         start_date=start_date,
                         end_date=end_date,
                         selected_period=period)


@reports_bp.route('/cash-flow')
def cash_flow():
    """Cash Flow report: includes loans and loan payments"""
    project_id = _get_project_id()
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

    # === CASH IN ===
    # Operating income
    income_total = calculate_total_income(start_date, end_date, project_id=project_id)

    # Loans received
    loans_received_query = db.session.query(func.sum(Loan.amount)).filter(
        Loan.project_id == project_id,
        Loan.received_date >= start_date,
        Loan.received_date <= end_date
    )
    loans_received = float(loans_received_query.scalar() or 0)

    total_cash_in = income_total + loans_received

    # === CASH OUT ===
    # All expenses (including building phase)
    expenses_total = calculate_total_expenses(start_date, end_date, project_id=project_id)

    # Loan payments
    loan_payments_query = db.session.query(func.sum(LoanPayment.amount)).join(Loan).filter(
        Loan.project_id == project_id,
        LoanPayment.payment_date >= start_date,
        LoanPayment.payment_date <= end_date
    )
    loan_payments_total = float(loan_payments_query.scalar() or 0)

    total_cash_out = expenses_total + loan_payments_total

    # Net Cash Flow
    net_cash_flow = total_cash_in - total_cash_out

    return render_template('reports/cash_flow.html',
                         income_total=income_total,
                         loans_received=loans_received,
                         total_cash_in=total_cash_in,
                         expenses_total=expenses_total,
                         loan_payments_total=loan_payments_total,
                         total_cash_out=total_cash_out,
                         net_cash_flow=net_cash_flow,
                         start_date=start_date,
                         end_date=end_date,
                         selected_period=period)


@reports_bp.route('/income-summary')
def income_summary():
    """Income summary by category for the selected project"""
    project_id = _get_project_id()
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
    project_id = _get_project_id()
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
    """Enhanced Equity Report: Owner Capital + Retained Earnings - Liabilities"""
    project_id = _get_project_id()
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    project = Project.query.get_or_404(project_id)

    # Owner Capital
    owner_capital = float(project.owner_capital or 0)

    # Total income (all time)
    total_income = calculate_total_income(project_id=project_id)

    # Total operating expenses (all time, operating phase only)
    operating_expenses_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating'
    )
    total_operating_expenses = float(operating_expenses_query.scalar() or 0)

    # Retained Earnings = Total Income - Total Operating Expenses
    retained_earnings = total_income - total_operating_expenses

    # Building costs (investment)
    building_costs_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'building'
    )
    building_costs = float(building_costs_query.scalar() or 0)

    # Liabilities: Unpaid loans + Debts owed by us
    unpaid_loans_query = db.session.query(func.sum(Loan.remaining_amount)).filter(
        Loan.project_id == project_id,
        Loan.is_paid == False
    )
    unpaid_loans = float(unpaid_loans_query.scalar() or 0)

    debts_by_us_query = db.session.query(func.sum(Debt.remaining_amount)).filter(
        Debt.project_id == project_id,
        Debt.debt_type == 'owed_by_us',
        Debt.is_paid == False
    )
    debts_by_us = float(debts_by_us_query.scalar() or 0)

    total_liabilities = unpaid_loans + debts_by_us

    # Assets: Account balances + Debts owed to us
    total_balance = calculate_total_balance(project_id=project_id)
    debts_to_us_query = db.session.query(func.sum(Debt.remaining_amount)).filter(
        Debt.project_id == project_id,
        Debt.debt_type == 'owed_to_us',
        Debt.is_paid == False
    )
    debts_to_us = float(debts_to_us_query.scalar() or 0)
    total_assets = total_balance + debts_to_us

    # Net Project Value = Owner Capital + Retained Earnings - Liabilities
    net_project_value = owner_capital + retained_earnings - total_liabilities

    return render_template('reports/equity.html',
                         project=project,
                         owner_capital=owner_capital,
                         retained_earnings=retained_earnings,
                         building_costs=building_costs,
                         unpaid_loans=unpaid_loans,
                         debts_by_us=debts_by_us,
                         total_liabilities=total_liabilities,
                         total_assets=total_assets,
                         debts_to_us=debts_to_us,
                         total_balance=total_balance,
                         net_project_value=net_project_value)


@reports_bp.route('/roi')
def roi_report():
    """ROI Report: Total Investment | Net Profit | ROI %"""
    project_id = _get_project_id()
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    project = Project.query.get_or_404(project_id)

    # Owner Capital
    owner_capital = float(project.owner_capital or 0)

    # Building costs
    building_costs_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'building'
    )
    building_costs = float(building_costs_query.scalar() or 0)

    # Total Investment = Owner Capital + Building Costs
    total_investment = owner_capital + building_costs

    # Total income (all time)
    total_income = calculate_total_income(project_id=project_id)

    # Operating expenses (all time)
    operating_expenses_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating'
    )
    total_operating_expenses = float(operating_expenses_query.scalar() or 0)

    # Net Profit = Total Income - Operating Expenses
    net_profit = total_income - total_operating_expenses

    # ROI % = (Net Profit / Total Investment) × 100
    roi_pct = (net_profit / total_investment * 100) if total_investment > 0 else 0

    return render_template('reports/roi.html',
                         project=project,
                         owner_capital=owner_capital,
                         building_costs=building_costs,
                         total_investment=total_investment,
                         total_income=total_income,
                         total_operating_expenses=total_operating_expenses,
                         net_profit=net_profit,
                         roi_pct=roi_pct)


@reports_bp.route('/kpis')
def kpis():
    """KPIs Dashboard"""
    project_id = _get_project_id()
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    project = Project.query.get_or_404(project_id)

    # Calculate time range for burn rate (last 6 months)
    today = date.today()
    six_months_ago = today - relativedelta(months=6)

    # Total operating expenses in last 6 months
    recent_expenses_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating',
        ExpenseTransaction.transaction_date >= six_months_ago,
        ExpenseTransaction.transaction_date <= today
    )
    recent_expenses = float(recent_expenses_query.scalar() or 0)

    # Count months with data
    months_query = db.session.query(
        func.distinct(func.strftime('%Y-%m', ExpenseTransaction.transaction_date))
    ).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating',
        ExpenseTransaction.transaction_date >= six_months_ago,
        ExpenseTransaction.transaction_date <= today
    )
    months_with_data = months_query.count() or 1

    # Burn Rate (average monthly operating expenses)
    burn_rate = recent_expenses / months_with_data

    # Current Cash (total account balances)
    total_cash = calculate_total_balance(project_id=project_id)

    # Runway (months of cash remaining at current burn rate)
    runway_months = (total_cash / burn_rate) if burn_rate > 0 else float('inf')

    # Total Income
    total_income = calculate_total_income(project_id=project_id)

    # Direct Costs (all time)
    direct_costs_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating',
        ExpenseTransaction.is_direct_cost == True
    )
    total_direct_costs = float(direct_costs_query.scalar() or 0)

    # Gross Profit & Margin
    gross_profit = total_income - total_direct_costs
    gross_margin_pct = (gross_profit / total_income * 100) if total_income > 0 else 0

    # Operating Expenses (all time)
    operating_expenses_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'operating',
        ExpenseTransaction.is_direct_cost == False
    )
    total_operating_expenses = float(operating_expenses_query.scalar() or 0)

    # Net Profit & Net Margin
    net_profit = gross_profit - total_operating_expenses
    net_margin_pct = (net_profit / total_income * 100) if total_income > 0 else 0

    # Total All Operating Expenses
    total_all_operating = total_direct_costs + total_operating_expenses

    # Operating Cost Ratio
    operating_cost_ratio = (total_all_operating / total_income * 100) if total_income > 0 else 0

    # ROI
    owner_capital = float(project.owner_capital or 0)
    building_costs_query = db.session.query(func.sum(ExpenseTransaction.amount)).filter(
        ExpenseTransaction.project_id == project_id,
        ExpenseTransaction.phase == 'building'
    )
    building_costs = float(building_costs_query.scalar() or 0)
    total_investment = owner_capital + building_costs
    roi_pct = (net_profit / total_investment * 100) if total_investment > 0 else 0

    return render_template('reports/kpis.html',
                         project=project,
                         burn_rate=burn_rate,
                         total_cash=total_cash,
                         runway_months=runway_months,
                         gross_margin_pct=gross_margin_pct,
                         net_margin_pct=net_margin_pct,
                         roi_pct=roi_pct,
                         operating_cost_ratio=operating_cost_ratio,
                         total_income=total_income,
                         total_direct_costs=total_direct_costs,
                         gross_profit=gross_profit,
                         total_operating_expenses=total_operating_expenses,
                         net_profit=net_profit,
                         total_investment=total_investment,
                         building_costs=building_costs,
                         owner_capital=owner_capital)
