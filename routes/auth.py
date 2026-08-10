from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os # 👈 YEH IMPORT ADD KIYA HAI
from models import User
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action') 
        
        if action == 'signup':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered! Please login.', 'error')
                return redirect(url_for('auth.login'))
                
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(name=name, email=email, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            
            session['user_id'] = new_user.id
            session['user_name'] = new_user.name
            session['is_admin'] = new_user.is_admin
            return redirect(url_for('main.dashboard'))
            
        elif action == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['is_admin'] = user.is_admin
                
                if user.is_admin:
                    return redirect(url_for('admin.admin_upload'))
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid email or password!', 'error')
                return redirect(url_for('auth.login'))

    # 🚀 SUPABASE KEYS FIX (Yahan se keys login.html mein jayengi)
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_ANON_KEY", "")
    
    return render_template('login.html', supabase_url=supabase_url, supabase_key=supabase_key)

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('is_admin', None)
    return redirect(url_for('main.home'))
