from flask import render_template, request, redirect, url_for, flash
from app.blueprints.income import income_bp
from app.models import db, IncomeTransaction, IncomeCategory, Account
from datetime import date


@income_bp.route('/')
def list_income():
    """List all income transactions"""
    page = request.args.get('page', 1, type=int)

    transactions = IncomeTransaction.query\
        .order_by(IncomeTransaction.transaction_date.desc())\
        .paginate(page=page, per_page=20, error_out=False)

    return render_template('income/list.html', transactions=transactions)


@income_bp.route('/add', methods=['GET', 'POST'])
def add_income():
    """Add new income transaction"""
    if request.method == 'POST':
        account_id = request.form.get('account_id', type=int)
        category_id = request.form.get('category_id', type=int)
        amount = request.form.get('amount', type=float)
        transaction_date_str = request.form.get('transaction_date')
        notes = request.form.get('notes', '').strip()

        if not all([account_id, category_id, amount, transaction_date_str]):
            flash('جميع الحقول مطلوبة', 'error')
            return redirect(url_for('income.add_income'))

        transaction = IncomeTransaction(
            account_id=account_id,
            category_id=category_id,
            amount=amount,
            transaction_date=date.fromisoformat(transaction_date_str),
            notes=notes
        )

        db.session.add(transaction)
        db.session.commit()

        account = Account.query.get(account_id)
        account.update_balance()

        flash('تم إضافة الدخل بنجاح', 'success')
        return redirect(url_for('income.list_income'))

    accounts = Account.query.filter_by(is_active=True).all()
    categories = IncomeCategory.query.filter_by(is_active=True).all()

    return render_template('income/add.html',
                         accounts=accounts,
                         categories=categories,
                         today=date.today())


@income_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_income(id):
    """Edit existing income transaction"""
    transaction = IncomeTransaction.query.get_or_404(id)
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

        flash('تم تحديث الدخل بنجاح', 'success')
        return redirect(url_for('income.list_income'))

    accounts = Account.query.filter_by(is_active=True).all()
    categories = IncomeCategory.query.filter_by(is_active=True).all()

    return render_template('income/edit.html',
                         transaction=transaction,
                         accounts=accounts,
                         categories=categories)


@income_bp.route('/delete/<int:id>', methods=['POST'])
def delete_income(id):
    """Delete income transaction"""
    transaction = IncomeTransaction.query.get_or_404(id)
    account_id = transaction.account_id

    db.session.delete(transaction)
    db.session.commit()

    Account.query.get(account_id).update_balance()

    flash('تم حذف الدخل بنجاح', 'success')
    return redirect(url_for('income.list_income'))
