from flask import render_template, request, redirect, url_for, flash, session
from app.blueprints.expenses import expenses_bp
from app.models import db, ExpenseTransaction, ExpenseCategory, Account, Project
from datetime import date


@expenses_bp.route('/')
def list_expenses():
    """List all expense transactions for the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)

    transactions = ExpenseTransaction.query\
        .filter_by(project_id=project_id)\
        .order_by(ExpenseTransaction.transaction_date.desc())\
        .paginate(page=page, per_page=20, error_out=False)

    return render_template('expenses/list.html', transactions=transactions)


@expenses_bp.route('/add', methods=['GET', 'POST'])
def add_expense():
    """Add new expense transaction to the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        account_id = request.form.get('account_id', type=int)
        category_id = request.form.get('category_id', type=int)
        amount = request.form.get('amount', type=float)
        transaction_date_str = request.form.get('transaction_date')
        notes = request.form.get('notes', '').strip()

        if not all([account_id, category_id, amount, transaction_date_str]):
            flash('جميع الحقول مطلوبة', 'error')
            return redirect(url_for('expenses.add_expense'))

        transaction = ExpenseTransaction(
            account_id=account_id,
            category_id=category_id,
            amount=amount,
            transaction_date=date.fromisoformat(transaction_date_str),
            notes=notes,
            project_id=project_id
        )

        db.session.add(transaction)
        db.session.commit()

        account = Account.query.get(account_id)
        account.update_balance()

        flash('تم إضافة المصروف بنجاح', 'success')
        return redirect(url_for('expenses.list_expenses'))

    accounts = Account.query.filter_by(
        project_id=project_id,
        is_active=True
    ).all()
    categories = ExpenseCategory.query.filter_by(is_active=True).all()

    return render_template('expenses/add.html',
                         accounts=accounts,
                         categories=categories,
                         today=date.today())


@expenses_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    """Edit existing expense transaction in the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    transaction = ExpenseTransaction.query.filter_by(
        id=id,
        project_id=project_id
    ).first_or_404()
    old_account_id = transaction.account_id

    if request.method == 'POST':
        transaction.account_id = request.form.get('account_id', type=int)
        transaction.category_id = request.form.get('category_id', type=int)
        transaction.amount = request.form.get('amount', type=float)
        transaction.transaction_date = date.fromisoformat(request.form.get('transaction_date'))
        transaction.notes = request.form.get('notes', '').strip()

        db.session.commit()

        if old_account_id != transaction.account_id:
            Account.query.get(old_account_id).update_balance()
        Account.query.get(transaction.account_id).update_balance()

        flash('تم تحديث المصروف بنجاح', 'success')
        return redirect(url_for('expenses.list_expenses'))

    accounts = Account.query.filter_by(
        project_id=project_id,
        is_active=True
    ).all()
    categories = ExpenseCategory.query.filter_by(is_active=True).all()

    return render_template('expenses/edit.html',
                         transaction=transaction,
                         accounts=accounts,
                         categories=categories)


@expenses_bp.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    """Delete expense transaction from the selected project"""
    project_id = session.get('selected_project_id')
    if not project_id:
        flash('يرجى اختيار مشروع أولاً', 'error')
        return redirect(url_for('main.index'))

    transaction = ExpenseTransaction.query.filter_by(
        id=id,
        project_id=project_id
    ).first_or_404()
    account_id = transaction.account_id

    db.session.delete(transaction)
    db.session.commit()

    Account.query.get(account_id).update_balance()

    flash('تم حذف المصروف بنجاح', 'success')
    return redirect(url_for('expenses.list_expenses'))
