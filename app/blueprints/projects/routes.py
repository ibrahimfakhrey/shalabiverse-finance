from flask import render_template, request, redirect, url_for, flash, session
from app.blueprints.projects import projects_bp
from app.models import db, Project
from app.utils import get_project_summary


@projects_bp.route('/')
def list_projects():
    """List all active projects"""
    projects = Project.query.filter_by(is_active=True)\
        .order_by(Project.created_at.desc()).all()
    return render_template('projects/list.html', projects=projects)


@projects_bp.route('/add', methods=['GET', 'POST'])
def add_project():
    """Add new project"""
    if request.method == 'POST':
        name_ar = request.form.get('name_ar', '').strip()
        name_en = request.form.get('name_en', '').strip()

        if not name_ar:
            flash('الاسم بالعربي مطلوب', 'error')
            return redirect(url_for('projects.add_project'))

        project = Project(name_ar=name_ar, name_en=name_en)
        project.set_pin('1234')  # Default PIN
        db.session.add(project)
        db.session.commit()

        flash('تم إضافة المشروع بنجاح', 'success')
        return redirect(url_for('projects.list_projects'))

    return render_template('projects/add.html')


@projects_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_project(id):
    """Edit project"""
    project = Project.query.get_or_404(id)

    if request.method == 'POST':
        project.name_ar = request.form.get('name_ar', '').strip()
        project.name_en = request.form.get('name_en', '').strip()

        if not project.name_ar:
            flash('الاسم بالعربي مطلوب', 'error')
            return redirect(url_for('projects.edit_project', id=id))

        db.session.commit()
        flash('تم تحديث المشروع بنجاح', 'success')
        return redirect(url_for('projects.list_projects'))

    return render_template('projects/edit.html', project=project)


@projects_bp.route('/delete/<int:id>', methods=['POST'])
def delete_project(id):
    """Soft delete project"""
    project = Project.query.get_or_404(id)

    # Check if project has data
    if project.accounts.count() > 0 or project.employees.count() > 0:
        flash('لا يمكن حذف المشروع لأنه يحتوي على بيانات', 'error')
        return redirect(url_for('projects.list_projects'))

    project.is_active = False
    db.session.commit()

    flash('تم حذف المشروع بنجاح', 'success')
    return redirect(url_for('projects.list_projects'))


@projects_bp.route('/select/<int:id>')
def select_project(id):
    """Select project - requires PIN verification"""
    project = Project.query.get_or_404(id)
    
    # If already verified in this session, go directly
    if session.get(f'project_{id}_verified'):
        session['selected_project_id'] = id
        session['selected_project_name'] = project.name_ar
        return redirect(url_for('main.project_dashboard', project_id=id))
    
    # Otherwise show PIN entry
    return redirect(url_for('projects.verify_pin', id=id))


@projects_bp.route('/verify-pin/<int:id>', methods=['GET', 'POST'])
def verify_pin(id):
    """PIN verification page for project access"""
    project = Project.query.get_or_404(id)
    
    if request.method == 'POST':
        pin = request.form.get('pin', '').strip()
        
        if project.check_pin(pin):
            session[f'project_{id}_verified'] = True
            session['selected_project_id'] = id
            session['selected_project_name'] = project.name_ar
            flash(f'تم الدخول إلى {project.name_ar}', 'success')
            return redirect(url_for('main.project_dashboard', project_id=id))
        else:
            flash('الرقم السري غير صحيح', 'error')
            return redirect(url_for('projects.verify_pin', id=id))
    
    return render_template('projects/verify_pin.html', project=project)


@projects_bp.route('/change-pin/<int:id>', methods=['GET', 'POST'])
def change_pin(id):
    """Change project PIN - requires old PIN"""
    project = Project.query.get_or_404(id)
    
    # Must be verified to change PIN
    if not session.get(f'project_{id}_verified'):
        flash('يجب الدخول للمشروع أولاً', 'error')
        return redirect(url_for('projects.verify_pin', id=id))
    
    if request.method == 'POST':
        old_pin = request.form.get('old_pin', '').strip()
        new_pin = request.form.get('new_pin', '').strip()
        confirm_pin = request.form.get('confirm_pin', '').strip()
        
        if not project.check_pin(old_pin):
            flash('الرقم السري القديم غير صحيح', 'error')
            return redirect(url_for('projects.change_pin', id=id))
        
        if not new_pin or len(new_pin) < 4:
            flash('الرقم السري الجديد يجب أن يكون 4 أرقام على الأقل', 'error')
            return redirect(url_for('projects.change_pin', id=id))
        
        if new_pin != confirm_pin:
            flash('الرقم السري الجديد غير متطابق', 'error')
            return redirect(url_for('projects.change_pin', id=id))
        
        project.set_pin(new_pin)
        db.session.commit()
        
        flash('تم تغيير الرقم السري بنجاح ✅', 'success')
        return redirect(url_for('main.project_dashboard', project_id=id))
    
    return render_template('projects/change_pin.html', project=project)
