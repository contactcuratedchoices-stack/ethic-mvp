from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import RegionalStory, User
from extensions import db

admin_bp = Blueprint('admin', __name__)

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def check_admin(user):
    return user and user.role in ['super_admin', 'editor']

# 🚀 1. MAIN ADMIN HUB (Options screen)
@admin_bp.route('/admin')
def admin_dashboard():
    user = get_current_user()
    if not check_admin(user):
        flash('ACCESS DENIED.', 'error')
        return redirect(url_for('main.dashboard'))
    
    db_count = RegionalStory.query.count()
    return render_template('admin_portal.html', view='dashboard', current_user=user, db_count=db_count)

# 🚀 2. UPLOAD SCREEN
@admin_bp.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    user = get_current_user()
    if not check_admin(user): return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', 'Untitled').strip()
        state = request.form.get('state').strip()
        moral = request.form.get('moral').strip() # Dropdown category
        specific_moral = request.form.get('specific_moral').strip() # The actual lesson
        core_story = request.form.get('core_story').strip()
        target_gender = request.form.get('target_gender', 'Any')
        min_age = request.form.get('min_age', 3)
        max_age = request.form.get('max_age', 10)
        theme = request.form.get('theme', 'General')
        
        new_story = RegionalStory(
            title=title, state=state, moral=moral, specific_moral=specific_moral, 
            core_story=core_story, target_gender=target_gender, 
            min_age=int(min_age), max_age=int(max_age), theme=theme
        )
        db.session.add(new_story)
        db.session.commit()
        
        flash(f'Success! "{title}" added to the database.', 'success')
        return redirect(url_for('admin.admin_upload'))
        
    return render_template('admin_portal.html', view='upload', current_user=user)

# 🚀 3. DATABASE SCREEN
@admin_bp.route('/admin/database')
def admin_database():
    user = get_current_user()
    if not check_admin(user): return redirect(url_for('main.dashboard'))
    
    stories = RegionalStory.query.order_by(RegionalStory.id.desc()).all()
    return render_template('admin_portal.html', view='database', current_user=user, stories=stories)

# 🚀 4. TEAM SCREEN (Super Admin Only)
@admin_bp.route('/admin/team')
def admin_team():
    user = get_current_user()
    if not user or user.role != 'super_admin':
        flash('Only Super Admins can access Team Management.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
        
    editors = User.query.filter_by(role='editor').all()
    return render_template('admin_portal.html', view='team', current_user=user, editors=editors)

# --- Action Routes ---
@admin_bp.route('/admin/delete_story/<int:story_id>', methods=['POST'])
def delete_story(story_id):
    user = get_current_user()
    if not user or user.role != 'super_admin': return redirect(url_for('admin.admin_dashboard'))

    story_to_delete = RegionalStory.query.get_or_404(story_id)
    db.session.delete(story_to_delete)
    db.session.commit()
    flash('Story removed from database!', 'success')
    return redirect(url_for('admin.admin_database'))

@admin_bp.route('/admin/add_editor', methods=['POST'])
def add_editor():
    user = get_current_user()
    if not user or user.role != 'super_admin': return redirect(url_for('admin.admin_dashboard'))
        
    email = request.form.get('email').strip()
    new_editor = User.query.filter_by(email=email).first()
    
    if not new_editor: flash(f'{email} not found. Ask them to sign up first.', 'error')
    elif new_editor.role in ['super_admin', 'editor']: flash(f'{email} is already an Admin/Editor.', 'error')
    else:
        new_editor.role = 'editor'
        db.session.commit()
        flash(f'{email} has been given Editor access!', 'success')
        
    return redirect(url_for('admin.admin_team'))

@admin_bp.route('/admin/remove_editor/<int:editor_id>', methods=['POST'])
def remove_editor(editor_id):
    user = get_current_user()
    if not user or user.role != 'super_admin': return redirect(url_for('admin.admin_dashboard'))
        
    editor = User.query.get_or_404(editor_id)
    if editor.role == 'editor':
        editor.role = 'user'
        db.session.commit()
        flash(f'Access revoked for {editor.email}.', 'success')
    return redirect(url_for('admin.admin_team'))
