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

    # 🚀 SUPABASE KEYS FIX (Passing to HTML)
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_ANON_KEY", "")
    
    return render_template('login.html', supabase_url=supabase_url, supabase_key=supabase_key)

# 🚀 NEW ROUTE: Bridging Supabase Frontend with Flask Backend
@auth_bp.route('/sync_session', methods=['POST'])
def sync_session():
    data = request.json
    email = data.get('email')
    name = data.get('name', 'User')

    if not email:
        return jsonify({"success": False, "error": "No email provided"}), 400

    # Check if user exists in local database
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # If logging in via Google for the first time, save to DB
        dummy_pw = generate_password_hash(os.urandom(24).hex(), method='pbkdf2:sha256')
        user = User(name=name, email=email, password=dummy_pw)
        db.session.add(user)
        db.session.commit()

    # Create the Flask session to allow access to /dashboard
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['is_admin'] = user.is_admin

    return jsonify({"success": True})

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('is_admin', None)
    return redirect(url_for('main.home'))
