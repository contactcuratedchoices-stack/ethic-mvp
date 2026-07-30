from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from groq import Groq
import os
import base64
from gtts import gTTS
import io
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Security & Database Config
app.secret_key = 'ethic_super_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ethic_v3.db' # 🚀 NAYA DATABASE v3
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Groq API Setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 🗄️ DATABASE MODELS 
# ==========================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False) # 🚀 NAYA FEATURE: Admin Role
    children = db.relationship('Child', backref='parent', lazy=True)
    stories = db.relationship('Story', backref='author', lazy=True)

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(20), nullable=False)
    native_place = db.Column(db.String(100), nullable=False)
    language = db.Column(db.String(50), nullable=False)

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    moral = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RegionalStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(100), nullable=False)
    moral = db.Column(db.String(100), nullable=False)
    core_story = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()
    # 🚀 JADU: Auto-Create Default Admin Account (ताकि तुम तुरंत टेस्ट कर सको)
    if not User.query.filter_by(email='admin@ethic.com').first():
        hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
        admin_user = User(name='Super Admin', email='admin@ethic.com', password=hashed_pw, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()

# ==========================================
# 🌐 WEBSITE ROUTES 
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to view your dashboard.', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_children = Child.query.filter_by(user_id=user_id).all()
    user_stories = Story.query.filter_by(user_id=user_id).order_by(Story.created_at.desc()).all()
    
    return render_template('dashboard.html', children=user_children, stories=user_stories)

@app.route('/studio')
def studio():
    if 'user_id' not in session:
        flash('Please log in or create an account to generate your first story.', 'error')
        return redirect(url_for('login'))
    
    user_children = Child.query.filter_by(user_id=session['user_id']).all()
    return render_template('studio.html', children=user_children)

@app.route('/story/<int:story_id>')
def read_story(story_id):
    if 'user_id' not in session:
        flash('Please log in to read stories.', 'error')
        return redirect(url_for('login'))
    
    story = Story.query.get_or_404(story_id)
    if story.user_id != session['user_id'] and not session.get('is_admin'):
        flash('Unauthorized access!', 'error')
        return redirect(url_for('dashboard'))
        
    return render_template('read_story.html', story=story)

# ==========================================
# 🔐 AUTHENTICATION ROUTES 
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
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
                return redirect(url_for('login'))
                
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(name=name, email=email, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            
            session['user_id'] = new_user.id
            session['user_name'] = new_user.name
            session['is_admin'] = new_user.is_admin # 🚀 सेव एडमिन स्टेटस
            return redirect(url_for('dashboard'))
            
        elif action == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['is_admin'] = user.is_admin # 🚀 सेव एडमिन स्टेटस
                
                # अगर एडमिन है, तो सीधा एडमिन पोर्टल पर भेज दो!
                if user.is_admin:
                    return redirect(url_for('admin_upload'))
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password!', 'error')
                return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('is_admin', None)
    return redirect(url_for('home'))

# ==========================================
# 🛠️ CMS ADMIN PORTAL (SECURED)
# ==========================================
@app.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    # 🔒 SECURITY CHECK: सिर्फ एडमिन ही इसे खोल सकता है
    if not session.get('is_admin'):
        flash('ACCESS DENIED: You do not have permission to view this page.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        state = request.form.get('state').strip()
        moral = request.form.get('moral')
        core_story = request.form.get('core_story').strip()
        
        new_regional_story = RegionalStory(state=state, moral=moral, core_story=core_story)
        db.session.add(new_regional_story)
        db.session.commit()
        
        flash(f'Success! Story for {state} added to the AI Database.', 'success')
        return redirect(url_for('admin_upload'))
        
    all_regional_stories = RegionalStory.query.order_by(RegionalStory.id.desc()).all()
    return render_template('admin_upload.html', stories=all_regional_stories)

# ==========================================
# ⚙️ API ROUTES (Data Handling & AI)
# ==========================================
@app.route('/add_child', methods=['POST'])
def add_child():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    name = request.form.get('child_name')
    age = request.form.get('age')
    native_place = request.form.get('native_place')
    language = request.form.get('language')
    
    new_child = Child(user_id=session['user_id'], name=name, age=age, native_place=native_place, language=language)
    db.session.add(new_child)
    db.session.commit()
    
    flash(f'{name} profile added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/generate_story', methods=['POST'])
def generate_story():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized. Please login."}), 401

    data = request.json
    child_name = data.get('child_name')
    native_place = data.get('native_place')
    age = data.get('age')
    moral_value = data.get('moral_value')
    language = data.get('language')
    wants_audio = data.get('generate_audio', False)
    
    language_instruction = ""
    if language == "Hindi":
        language_instruction = "CRITICAL RULE: YOU MUST WRITE THE ENTIRE STORY STRICTLY IN PURE HINDI USING THE DEVANAGARI SCRIPT."
    elif language == "Hinglish":
        language_instruction = "CRITICAL RULE: WRITE THE ENTIRE STORY IN HINGLISH."
    else:
        language_instruction = "CRITICAL RULE: WRITE THE ENTIRE STORY IN ENGLISH."

    regional_base = RegionalStory.query.filter_by(state=native_place, moral=moral_value).first()
    
    regional_context = ""
    if regional_base:
        regional_context = f"""
        CRITICAL INSTRUCTION: I am providing you an authentic regional folktale from {native_place}. 
        You MUST base your entire response strictly on this story: '{regional_base.core_story}'.
        Do not invent a new plot. Just replace the main character's name with '{child_name}' and adapt the tone for a {age}-year-old.
        """
    else:
        regional_context = f"Invent a culturally accurate folktale from {native_place} teaching {moral_value}."

    system_prompt = "You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller."
    user_prompt = f"""
    Write a highly personalized, emotional bedtime story for your {age}-year-old grandchild named {child_name}.
    Core Moral to teach: "{moral_value}". Native Place: "{native_place}".
    {language_instruction}
    {regional_context}
    RULES: Add cultural depth. Tone must match a {age}-year-old. Add a warm grandparent greeting. End with a real-world task. Length: 350-400 words.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
        )
        story_text = response.choices[0].message.content
        title = f"{child_name}'s Tale of {moral_value}"
        
        new_story = Story(user_id=session['user_id'], title=title, content=story_text, moral=moral_value)
        db.session.add(new_story)
        db.session.commit()
        
        audio_base64 = None
        audio_error = None
        
        if wants_audio:
            try:
                tts_lang = 'hi' if language == 'Hindi' else 'en'
                tts = gTTS(text=story_text, lang=tts_lang, slow=False)
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
            except Exception as e:
                audio_error = f"Free TTS Error: {str(e)}"

        return jsonify({
            "success": True, 
            "story": story_text,
            "title": title,
            "audio_base64": audio_base64,
            "audio_error": audio_error
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
