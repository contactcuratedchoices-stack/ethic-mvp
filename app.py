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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ethic_database.db' # नाम बदल दिया ताकि नया फ्रेश DB बने
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Groq API Setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 🗄️ UPGRADED DATABASE MODELS 
# ==========================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # रिलेशनशिप: एक यूजर के कई बच्चे और कई कहानियां हो सकती हैं
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

# डेटाबेस टेबल्स क्रिएट करना
with app.app_context():
    db.create_all()

# ==========================================
# 🌐 WEBSITE ROUTES 
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# 🚨 THE LOCK: यूजर का डैशबोर्ड
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to view your dashboard.', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    # यूजर के बच्चे और पुरानी कहानियां डेटाबेस से निकालो
    user_children = Child.query.filter_by(user_id=user_id).all()
    user_stories = Story.query.filter_by(user_id=user_id).order_by(Story.created_at.desc()).all()
    
    return render_template('dashboard.html', children=user_children, stories=user_stories)

# 🚨 THE LOCK: स्टोरी स्टूडियो
@app.route('/studio')
def studio():
    if 'user_id' not in session:
        flash('Please log in or create an account to generate your first story.', 'error')
        return redirect(url_for('login'))
    
    # फॉर्म में ड्रॉपडाउन के लिए बच्चों की लिस्ट भेजो
    user_children = Child.query.filter_by(user_id=session['user_id']).all()
    return render_template('studio.html', children=user_children)

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
            return redirect(url_for('dashboard')) # साइन-अप के बाद डैशबोर्ड पर भेजो
            
        elif action == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                return redirect(url_for('dashboard')) # लॉग-इन के बाद डैशबोर्ड पर भेजो
            else:
                flash('Invalid email or password!', 'error')
                return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    return redirect(url_for('home'))

# ==========================================
# ⚙️ API ROUTES (Data Handling)
# ==========================================

# नया बच्चा ऐड करने का API
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

    system_prompt = "You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller."
    user_prompt = f"""
    Write a highly personalized, emotional bedtime story for your {age}-year-old grandchild named {child_name}.
    Core Moral to teach: "{moral_value}". Native Place: "{native_place}".
    {language_instruction}
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
        
        # 💾 कहानी को डेटाबेस में सेव करना
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
