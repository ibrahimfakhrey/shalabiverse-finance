from flask import render_template, request, redirect, url_for, flash
from app.blueprints.accounts import accounts_bp
from app.models import db, Account, AccountType
from datetime import date


@accounts_bp.route('/')
def list_accounts():
    """List all accounts"""
    accounts = Account.query.filter_by(is_active=True).all()
    return render_template('accounts/list.html', accounts=accounts)


@accounts_bp.route('/add', methods=['GET', 'POST'])
def add_account():
    """Add new account"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        account_type_id = request.form.get('account_type_id', type=int)
        initial_balance = request.form.get('initial_balance', type=float, default=0.00)

        if not all([name, account_type_id is not None]):
            flash('الاسم ونوع الحساب مطلوبان', 'error')
            return redirect(url_for('accounts.add_account'))

        account = Account(
            name=name,
            account_type_id=account_type_id,
            initial_balance=initial_balance,
            current_balance=initial_balance
        )

        db.session.add(account)
        db.session.commit()

        flash('تم إضافة الحساب بنجاح', 'success')
        return redirect(url_for('accounts.list_accounts'))

    account_types = AccountType.query.all()
    return render_template('accounts/add.html', account_types=account_types)


@accounts_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_account(id):
    """Edit existing account"""
    account = Account.query.get_or_404(id)

    if request.method == 'POST':
        account.name = request.form.get('name', '').strip()
        account.account_type_id = request.form.get('account_type_id', type=int)

        db.session.commit()

        flash('تم تحديث الحساب بنجاح', 'success')
        return redirect(url_for('accounts.list_accounts'))

    account_types = AccountType.query.all()
    return render_template('accounts/edit.html', account=account, account_types=account_types)


@accounts_bp.route('/delete/<int:id>', methods=['POST'])
def delete_account(id):
    """Deactivate account"""
    account = Account.query.get_or_404(id)
    account.is_active = False
    db.session.commit()

    flash('تم حذف الحساب بنجاح', 'success')
    return redirect(url_for('accounts.list_accounts'))


@accounts_bp.route('/details/<int:id>')
def account_details(id):
    """View account details and transaction history"""
    account = Account.query.get_or_404(id)
    account.update_balance()
    return render_template('accounts/details.html', account=account)
