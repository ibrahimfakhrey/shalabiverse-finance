from flask import render_template, request, redirect, url_for, flash, session
from app.blueprints.debts import debts_bp
from app.models import db, Debt, DebtPayment, Account, Project
from datetime import date


@debts_bp.route('/')
def list_debts():
    """List all debts for the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    debt_type = request.args.get('type', 'all')
    status = request.args.get('status', 'all')

    query = Debt.query.filter_by(project_id=project_id)

    if debt_type != 'all':
        query = query.filter_by(debt_type=debt_type)

    if status == 'unpaid':
        query = query.filter_by(payment_status='unpaid')
    elif status == 'partial':
        query = query.filter_by(payment_status='partial')
    elif status == 'paid':
        query = query.filter_by(payment_status='paid')

    debts = query.order_by(Debt.due_date.asc()).all()

    total_owed_to_us = sum(float(d.remaining_amount) for d in debts if d.debt_type == 'owed_to_us' and not d.is_paid)
    total_owed_by_us = sum(float(d.remaining_amount) for d in debts if d.debt_type == 'owed_by_us' and not d.is_paid)

    return render_template('debts/list.html',
                         debts=debts,
                         total_owed_to_us=total_owed_to_us,
                         total_owed_by_us=total_owed_by_us,
                         debt_type_filter=debt_type,
                         status_filter=status)


@debts_bp.route('/add', methods=['GET', 'POST'])
def add_debt():
    """Add new debt to the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        debt_type = request.form.get('debt_type')
        person_name = request.form.get('person_name', '').strip()
        amount = request.form.get('amount', type=float)
        account_id = request.form.get('account_id', type=int)
        due_date_str = request.form.get('due_date')
        notes = request.form.get('notes', '').strip()

        if not all([debt_type, person_name, amount]):
            flash('الحقول المطلوبة: نوع الدين، اسم الشخص، المبلغ', 'error')
            return redirect(url_for('debts.add_debt'))

        due_date_val = date.fromisoformat(due_date_str) if due_date_str else None

        debt = Debt(
            debt_type=debt_type,
            person_name=person_name,
            original_amount=amount,
            remaining_amount=amount,
            account_id=account_id,
            due_date=due_date_val,
            notes=notes,
            project_id=project_id
        )

        db.session.add(debt)
        db.session.commit()

        # Update account balance (debt affects cash)
        if account_id:
            account = Account.query.get(account_id)
            if account:
                account.update_balance()

        flash('تم إضافة الدين بنجاح وتم تحديث الرصيد', 'success')
        return redirect(url_for('debts.list_debts'))

    accounts = Account.query.filter_by(project_id=project_id, is_active=True).all()
    return render_template('debts/add.html', today=date.today(), accounts=accounts)


@debts_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_debt(id):
    """Edit existing debt in the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    debt = Debt.query.filter_by(
        id=id,
        project_id=project_id
    ).first_or_404()

    if request.method == 'POST':
        debt.person_name = request.form.get('person_name', '').strip()
        debt.due_date = date.fromisoformat(request.form.get('due_date')) if request.form.get('due_date') else None
        debt.notes = request.form.get('notes', '').strip()

        db.session.commit()

        flash('تم تحديث الدين بنجاح', 'success')
        return redirect(url_for('debts.list_debts'))

    return render_template('debts/edit.html', debt=debt)


@debts_bp.route('/payment/<int:id>', methods=['GET', 'POST'])
def record_payment(id):
    """Record debt payment for the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    debt = Debt.query.filter_by(
        id=id,
        project_id=project_id
    ).first_or_404()

    if request.method == 'POST':
        amount = request.form.get('amount', type=float)
        payment_date_str = request.form.get('payment_date')
        account_id = request.form.get('account_id', type=int)
        notes = request.form.get('notes', '').strip()

        if not amount or amount <= 0:
            flash('المبلغ غير صحيح', 'error')
            return redirect(url_for('debts.record_payment', id=id))

        if amount > float(debt.remaining_amount):
            flash('المبلغ أكبر من المتبقي من الدين', 'error')
            return redirect(url_for('debts.record_payment', id=id))

        payment_date_val = date.fromisoformat(payment_date_str) if payment_date_str else date.today()

        payment = DebtPayment(
            debt_id=debt.id,
            amount=amount,
            payment_date=payment_date_val,
            account_id=account_id,
            notes=notes
        )

        db.session.add(payment)

        debt.remaining_amount = float(debt.remaining_amount) - amount
        debt.update_status()

        db.session.commit()

        # Recalculate balance for the payment account
        if account_id:
            Account.query.get(account_id).update_balance()
        # Also recalculate the original debt account if different
        if debt.account_id and debt.account_id != account_id:
            Account.query.get(debt.account_id).update_balance()

        flash('تم تسجيل الدفعة بنجاح وتم تحديث الرصيد', 'success')
        return redirect(url_for('debts.list_debts'))

    accounts = Account.query.filter_by(
        project_id=project_id,
        is_active=True
    ).all()
    return render_template('debts/payment.html',
                         debt=debt,
                         accounts=accounts,
                         today=date.today())


@debts_bp.route('/delete/<int:id>', methods=['POST'])
def delete_debt(id):
    """Delete debt from the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    debt = Debt.query.filter_by(
        id=id,
        project_id=project_id
    ).first_or_404()
    account_id = debt.account_id
    db.session.delete(debt)
    db.session.commit()

    # Recalculate balance after deleting debt
    if account_id:
        account = Account.query.get(account_id)
        if account:
            account.update_balance()

    flash('تم حذف الدين بنجاح', 'success')
    return redirect(url_for('debts.list_debts'))
