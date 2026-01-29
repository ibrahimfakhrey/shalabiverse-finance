from flask import render_template, request, redirect, url_for, flash, session
from app.blueprints.loans import loans_bp
from app.models import db, Loan, LoanPayment, Account, Project
from datetime import date


@loans_bp.route('/')
def list_loans():
    """List all loans for the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    status = request.args.get('status', 'all')

    query = Loan.query.filter_by(project_id=project_id)

    if status == 'unpaid':
        query = query.filter_by(is_paid=False)
    elif status == 'paid':
        query = query.filter_by(is_paid=True)

    loans = query.order_by(Loan.created_at.desc()).all()

    total_loans = sum(float(l.amount) for l in loans)
    total_remaining = sum(float(l.remaining_amount) for l in loans if not l.is_paid)
    total_paid = total_loans - total_remaining

    return render_template('loans/list.html',
                         loans=loans,
                         total_loans=total_loans,
                         total_remaining=total_remaining,
                         total_paid=total_paid,
                         status_filter=status)


@loans_bp.route('/add', methods=['GET', 'POST'])
def add_loan():
    """Add new loan to the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        lender_name = request.form.get('lender_name', '').strip()
        amount = request.form.get('amount', type=float)
        account_id = request.form.get('account_id', type=int)
        received_date_str = request.form.get('received_date')
        due_date_str = request.form.get('due_date')
        interest_rate = request.form.get('interest_rate', type=float, default=0.0)
        notes = request.form.get('notes', '').strip()

        if not all([lender_name, amount, account_id, received_date_str]):
            flash('الحقول المطلوبة: اسم المُقرض، المبلغ، الحساب، تاريخ الاستلام', 'error')
            return redirect(url_for('loans.add_loan'))

        received_date_val = date.fromisoformat(received_date_str)
        due_date_val = date.fromisoformat(due_date_str) if due_date_str else None

        # Create the loan
        loan = Loan(
            project_id=project_id,
            lender_name=lender_name,
            amount=amount,
            remaining_amount=amount,
            received_date=received_date_val,
            due_date=due_date_val,
            interest_rate=interest_rate or 0.0,
            account_id=account_id,
            notes=notes
        )

        db.session.add(loan)

        # CRITICAL: Increase account balance (loan is NOT income)
        account = Account.query.get(account_id)
        account.current_balance = float(account.current_balance) + amount

        db.session.commit()

        flash('تم إضافة القرض بنجاح وتم تحديث رصيد الحساب', 'success')
        return redirect(url_for('loans.list_loans'))

    accounts = Account.query.filter_by(
        project_id=project_id,
        is_active=True
    ).all()

    return render_template('loans/add.html',
                         accounts=accounts,
                         today=date.today())


@loans_bp.route('/<int:id>')
def loan_detail(id):
    """View loan details with payment history"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    loan = Loan.query.filter_by(id=id, project_id=project_id).first_or_404()
    payments = loan.payments.order_by(LoanPayment.payment_date.desc()).all()

    accounts = Account.query.filter_by(
        project_id=project_id,
        is_active=True
    ).all()

    return render_template('loans/detail.html',
                         loan=loan,
                         payments=payments,
                         accounts=accounts,
                         today=date.today())


@loans_bp.route('/<int:id>/pay', methods=['POST'])
def pay_loan(id):
    """Make a loan payment - DOES NOT create expense, DOES NOT affect P&L"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    loan = Loan.query.filter_by(id=id, project_id=project_id).first_or_404()

    amount = request.form.get('amount', type=float)
    account_id = request.form.get('account_id', type=int)
    payment_date_str = request.form.get('payment_date')
    notes = request.form.get('notes', '').strip()

    if not amount or amount <= 0:
        flash('المبلغ غير صحيح', 'error')
        return redirect(url_for('loans.loan_detail', id=id))

    if amount > float(loan.remaining_amount):
        flash('المبلغ أكبر من المتبقي من القرض', 'error')
        return redirect(url_for('loans.loan_detail', id=id))

    if not account_id:
        flash('يرجى اختيار حساب الدفع', 'error')
        return redirect(url_for('loans.loan_detail', id=id))

    payment_date_val = date.fromisoformat(payment_date_str) if payment_date_str else date.today()

    # Create loan payment record
    payment = LoanPayment(
        loan_id=loan.id,
        amount=amount,
        payment_date=payment_date_val,
        account_id=account_id,
        notes=notes
    )
    db.session.add(payment)

    # CRITICAL: Decrease account balance (loan payment is NOT expense)
    account = Account.query.get(account_id)
    account.current_balance = float(account.current_balance) - amount

    # Decrease remaining amount on loan
    loan.remaining_amount = float(loan.remaining_amount) - amount
    loan.update_status()

    db.session.commit()

    flash('تم تسجيل دفعة القرض بنجاح', 'success')
    return redirect(url_for('loans.loan_detail', id=id))


@loans_bp.route('/<int:id>/delete', methods=['POST'])
def delete_loan(id):
    """Delete a loan"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    loan = Loan.query.filter_by(id=id, project_id=project_id).first_or_404()

    # Reverse the account balance effect (subtract the original amount, add back payments)
    total_payments = sum(float(p.amount) for p in loan.payments.all())
    net_effect = float(loan.amount) - total_payments  # what's still in the account from this loan

    account = Account.query.get(loan.account_id)
    if account:
        account.current_balance = float(account.current_balance) - net_effect

    db.session.delete(loan)
    db.session.commit()

    flash('تم حذف القرض بنجاح', 'success')
    return redirect(url_for('loans.list_loans'))
