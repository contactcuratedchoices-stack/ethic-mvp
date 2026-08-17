from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import RegionalStory, User
from extensions import db

admin_bp = Blueprint('admin', __name__)

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@admin_bp.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    user = get_current_user()
    
    # 🔒 CLEANED: अब सिर्फ role चेक होगा, is_admin का नामोनिशान मिटा दिया
    if not user or user.role not in ['super_admin', 'editor']:
        flash('ACCESS DENIED: You do not have permission to view this page.', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        state = request.form.get('state').strip()
        moral = request.form.get('moral')
        core_story = request.form.get('core_story').strip()
        target_gender = request.form.get('target_gender', 'Any')
        min_age = request.form.get('min_age', 3)
        max_age = request.form.get('max_age', 10)
        theme = request.form.get('theme', 'General')
        
        new_regional_story = RegionalStory(
            state=state, 
            moral=moral, 
            core_story=core_story,
            target_gender=target_gender,
            min_age=int(min_age),
            max_age=int(max_age),
            theme=theme
        )
        db.session.add(new_regional_story)
        db.session.commit()
        
        flash(f'Success! {theme} story for {target_gender} added.', 'success')
        return redirect(url_for('admin.admin_upload'))
        
    all_regional_stories = RegionalStory.query.order_by(RegionalStory.id.desc()).all()
    
    # Editors list (Only passed to UI if user is super_admin)
    editors = User.query.filter_by(role='editor').all() if user.role == 'super_admin' else []
    
    return render_template('admin_upload.html', stories=all_regional_stories, current_user=user, editors=editors)


@admin_bp.route('/admin/delete_story/<int:story_id>', methods=['POST'])
def delete_story(story_id):
    user = get_current_user()
    if not user or user.role != 'super_admin':
        flash('Only Super Admins can delete stories.', 'error')
        return redirect(url_for('admin.admin_upload'))

    story_to_delete = RegionalStory.query.get_or_404(story_id)
    db.session.delete(story_to_delete)
    db.session.commit()

    flash('Story successfully removed from database!', 'success')
    return redirect(url_for('admin.admin_upload'))


@admin_bp.route('/admin/add_editor', methods=['POST'])
def add_editor():
    user = get_current_user()
    if not user or user.role != 'super_admin':
        flash('Only Super Admins can add team members.', 'error')
        return redirect(url_for('admin.admin_upload'))
        
    email = request.form.get('email').strip()
    new_editor = User.query.filter_by(email=email).first()
    
    if not new_editor:
        flash(f'User with email {email} not found. Ask them to sign up on ETHIC first.', 'error')
    elif new_editor.role == 'super_admin':
        flash(f'{email} is already a Super Admin.', 'error')
    elif new_editor.role == 'editor':
        flash(f'{email} is already an Editor.', 'error')
    else:
        new_editor.role = 'editor'
        db.session.commit()
        flash(f'{email} has been given Editor access successfully!', 'success')
        
    return redirect(url_for('admin.admin_upload'))


@admin_bp.route('/admin/remove_editor/<int:editor_id>', methods=['POST'])
def remove_editor(editor_id):
    user = get_current_user()
    if not user or user.role != 'super_admin':
        flash('Only Super Admins can remove team members.', 'error')
        return redirect(url_for('admin.admin_upload'))
        
    editor = User.query.get_or_404(editor_id)
    if editor.role == 'editor':
        editor.role = 'user'
        db.session.commit()
        flash(f'Access revoked for {editor.email}. They are now a normal user.', 'success')
    
    return redirect(url_for('admin.admin_upload'))
