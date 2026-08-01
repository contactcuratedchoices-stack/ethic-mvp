from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import RegionalStory
from extensions import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    if not session.get('is_admin'):
        flash('ACCESS DENIED: You do not have permission to view this page.', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        state = request.form.get('state').strip()
        moral = request.form.get('moral')
        core_story = request.form.get('core_story').strip()
        
        new_regional_story = RegionalStory(state=state, moral=moral, core_story=core_story)
        db.session.add(new_regional_story)
        db.session.commit()
        
        flash(f'Success! Story for {state} added to the AI Database.', 'success')
        return redirect(url_for('admin.admin_upload'))
        
    all_regional_stories = RegionalStory.query.order_by(RegionalStory.id.desc()).all()
    return render_template('admin_upload.html', stories=all_regional_stories)
