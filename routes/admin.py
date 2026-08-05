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
        
        # 🚀 NAYE FIELDS
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
    return render_template('admin_upload.html', stories=all_regional_stories)

# 🚀 NAYA ROUTE: KAHANI DELETE KARNE KE LIYE
@admin_bp.route('/admin/delete_story/<int:story_id>', methods=['POST'])
def delete_story(story_id):
    if not session.get('is_admin'):
        return redirect(url_for('main.dashboard'))

    story_to_delete = RegionalStory.query.get_or_404(story_id)
    db.session.delete(story_to_delete)
    db.session.commit()

    flash('Story successfully removed from database!', 'success')
    return redirect(url_for('admin.admin_upload'))
