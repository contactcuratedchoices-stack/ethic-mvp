from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from groq import Groq
import os
import base64
from gtts import gTTS
import io
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Security & Database Config
app.secret_key = 'ethic_super_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ethic_users.db'
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

with app.app_context():
    db.create_all()

# ==========================================
# 🌐 WEBSITE ROUTES 
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

# 🚨 THE LOCK: यह कोड चेक करेगा कि यूजर लॉगिन है या नहीं
@app.route('/studio')
def studio():
    if 'user_id' not in session:
        flash('Please log in or create an account to generate your first story.', 'error')
        return redirect(url_for('login'))
    return render_template('studio.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

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
            return redirect(url_for('studio'))
            
        elif action == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                return redirect(url_for('studio'))
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
# ⚙️ API ROUTES 
# ==========================================
@app.route('/generate_story', methods=['POST'])
def generate_story():
    # सिक्यूरिटी: अगर कोई बिना लॉगिन के API कॉल करे तो रोक दो (Advanced)
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized. Please login."}), 401

    data = request.json
    child_name = data.get('child_name')
    native_place = data.get('native_place')
    age = data.get('age')
    gender = data.get('gender')
    moral_value = data.get('moral_value')
    language = data.get('language')
    wants_audio = data.get('generate_audio', False)
    
    language_instruction = ""
    if language == "Hindi":
        language_instruction = "CRITICAL RULE: YOU MUST WRITE THE ENTIRE STORY STRICTLY IN PURE HINDI USING THE DEVANAGARI SCRIPT. DO NOT USE ENGLISH LETTERS FOR HINDI."
    elif language == "Hinglish":
        language_instruction = "CRITICAL RULE: WRITE THE ENTIRE STORY IN HINGLISH."
    else:
        language_instruction = "CRITICAL RULE: WRITE THE ENTIRE STORY IN ENGLISH."

    system_prompt = "You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller."
    user_prompt = f"""
    Write a highly personalized, emotional bedtime story for your {age}-year-old {gender} grandchild named {child_name}.
    Core Moral to teach: "{moral_value}". Native Place: "{native_place}".
    {language_instruction}
    RULES: Add cultural depth. Tone must match a {age}-year-old. Add a warm grandparent greeting. Relatable struggle before doing the right thing. End with a real-world task. Length: 350-400 words.
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
            "audio_base64": audio_base64,
            "audio_error": audio_error
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
