from flask import render_template, request, redirect, url_for, flash
from app.blueprints.employees import employees_bp
from app.models import db, Employee, SalaryPayment, ExpenseTransaction, ExpenseCategory, Account
from datetime import date


@employees_bp.route('/')
def list_employees():
    """List all employees"""
    employees = Employee.query.filter_by(is_active=True).all()
    return render_template('employees/list.html', employees=employees)


@employees_bp.route('/add', methods=['GET', 'POST'])
def add_employee():
    """Add new employee"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        base_salary = request.form.get('base_salary', type=float)
        hire_date_str = request.form.get('hire_date')
        notes = request.form.get('notes', '').strip()

        if not all([name, base_salary]):
            flash('الاسم والراتب الأساسي مطلوبان', 'error')
            return redirect(url_for('employees.add_employee'))

        hire_date_val = date.fromisoformat(hire_date_str) if hire_date_str else None

        employee = Employee(
            name=name,
            base_salary=base_salary,
            hire_date=hire_date_val,
            notes=notes
        )

        db.session.add(employee)
        db.session.commit()

        flash('تم إضافة الموظف بنجاح', 'success')
        return redirect(url_for('employees.list_employees'))

    return render_template('employees/add.html', today=date.today())


@employees_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    """Edit existing employee"""
    employee = Employee.query.get_or_404(id)

    if request.method == 'POST':
        employee.name = request.form.get('name', '').strip()
        employee.base_salary = request.form.get('base_salary', type=float)
        employee.hire_date = date.fromisoformat(request.form.get('hire_date')) if request.form.get('hire_date') else None
        employee.notes = request.form.get('notes', '').strip()

        db.session.commit()

        flash('تم تحديث بيانات الموظف بنجاح', 'success')
        return redirect(url_for('employees.list_employees'))

    return render_template('employees/edit.html', employee=employee)


@employees_bp.route('/delete/<int:id>', methods=['POST'])
def delete_employee(id):
    """Deactivate employee"""
    employee = Employee.query.get_or_404(id)
    employee.is_active = False
    db.session.commit()

    flash('تم حذف الموظف بنجاح', 'success')
    return redirect(url_for('employees.list_employees'))


@employees_bp.route('/salary-payment/<int:employee_id>', methods=['GET', 'POST'])
def salary_payment(employee_id):
    """Record salary payment for employee"""
    employee = Employee.query.get_or_404(employee_id)

    if request.method == 'POST':
        payment_date_str = request.form.get('payment_date')
        base_salary = request.form.get('base_salary', type=float)
        deductions = request.form.get('deductions', type=float, default=0.00)
        bonus = request.form.get('bonus', type=float, default=0.00)
        commission = request.form.get('commission', type=float, default=0.00)
        account_id = request.form.get('account_id', type=int)
        notes = request.form.get('notes', '').strip()

        if not all([base_salary, account_id]):
            flash('الراتب الأساسي والحساب مطلوبان', 'error')
            return redirect(url_for('employees.salary_payment', employee_id=employee_id))

        payment_date_val = date.fromisoformat(payment_date_str) if payment_date_str else date.today()

        salary_payment_obj = SalaryPayment(
            employee_id=employee_id,
            payment_date=payment_date_val,
            base_salary=base_salary,
            deductions=deductions,
            bonus=bonus,
            commission=commission,
            notes=notes
        )

        salary_payment_obj.calculate_net_salary()

        salary_category = ExpenseCategory.query.filter_by(name_en='salaries').first()

        expense = ExpenseTransaction(
            account_id=account_id,
            category_id=salary_category.id if salary_category else 1,
            amount=salary_payment_obj.net_salary,
            transaction_date=payment_date_val,
            notes=f'راتب {employee.name} - {notes}',
            is_salary=True,
            employee_id=employee_id
        )

        db.session.add(expense)
        db.session.flush()

        salary_payment_obj.expense_transaction_id = expense.id
        db.session.add(salary_payment_obj)
        db.session.commit()

        Account.query.get(account_id).update_balance()

        flash('تم تسجيل صرف الراتب بنجاح', 'success')
        return redirect(url_for('employees.list_employees'))

    accounts = Account.query.filter_by(is_active=True).all()
    return render_template('employees/salary_payment.html',
                         employee=employee,
                         accounts=accounts,
                         today=date.today())
