from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
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
            # 🚀 CLEANED: is_admin removed
            new_user = User(name=name, email=email, password=hashed_pw, role='user')
            db.session.add(new_user)
            db.session.commit()
            
            session['user_id'] = new_user.id
            session['user_name'] = new_user.name if new_user.name else "User"
            session['role'] = new_user.role
            return redirect(url_for('main.dashboard'))
            
        elif action == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            # 🚀 FIX: Handle users who signed up with Google (password might be null)
            if user and user.password and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user_name'] = user.name if user.name else "User"
                session['role'] = user.role
                
                # 🚀 CLEANED: Role checking instead of is_admin
                if user.role in ['super_admin', 'editor']:
                    return redirect(url_for('admin.admin_upload'))
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid email or password!', 'error')
                return redirect(url_for('auth.login'))

    # 🚀 SUPABASE KEYS FIX
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_ANON_KEY", "")
    
    return render_template('login.html', supabase_url=supabase_url, supabase_key=supabase_key)

@auth_bp.route('/sync_session', methods=['POST'])
def sync_session():
    data = request.json
    email = data.get('email')
    name = data.get('name', 'User')

    if not email:
        return jsonify({"success": False, "error": "No email provided"}), 400

    user = User.query.filter_by(email=email).first()
    
    if not user:
        # 🚀 FIX: Since password is now nullable=True in DB, we don't need dummy hash
        user = User(name=name, email=email, role='user')
        db.session.add(user)
        db.session.commit()
    elif user and not user.name and name and name != "User":
        # 🚀 FIX: If user logs in with Google and name was empty, update it
        user.name = name
        db.session.commit()

    # 🚀 CRITICAL BUG FIX: is_admin hata diya, ab 'role' use hoga
    session['user_id'] = user.id
    session['user_name'] = user.name if user.name else "User"
    session['role'] = user.role

    return jsonify({"success": True})

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('role', None)
    session.pop('is_admin', None) # Removing legacy key securely
    return redirect(url_for('main.home'))
