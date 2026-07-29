from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
import base64
from gtts import gTTS
import io

app = Flask(__name__)

# Groq API Setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 🌐 WEBSITE ROUTES (मल्टी-पेज नेविगेशन)
# ==========================================

# 1. Home Page (मार्केटिंग और ट्रस्ट बिल्डिंग)
@app.route('/')
def home():
    return render_template('index.html')

# 2. Story Studio Page (जहाँ फॉर्म और प्लेयर होगा)
@app.route('/studio')
def studio():
    return render_template('studio.html')

# 3. Pricing & Plans Page (IQ, EQ और पैकेजेस)
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# 4. Login Page (यूजर ऑथेंटिकेशन के लिए)
@app.route('/login')
def login():
    return render_template('login.html')

# ==========================================
# ⚙️ API ROUTES (बैकएंड लॉजिक)
# ==========================================

@app.route('/generate_story', methods=['POST'])
def generate_story():
    data = request.json
    child_name = data.get('child_name')
    native_place = data.get('native_place')
    age = data.get('age')
    gender = data.get('gender')
    moral_value = data.get('moral_value')
    language = data.get('language')
    
    wants_audio = data.get('generate_audio', False)
    
    # 🚨 THE BRAHMASTRA: Strict Language Lock
    language_instruction = ""
    if language == "Hindi":
        language_instruction = """
        CRITICAL RULE: YOU MUST WRITE THE ENTIRE STORY STRICTLY IN PURE HINDI USING THE DEVANAGARI SCRIPT (हिंदी लिपि). 
        DO NOT USE ENGLISH LETTERS FOR HINDI. 
        """
    elif language == "Hinglish":
        language_instruction = """
        CRITICAL RULE: WRITE THE ENTIRE STORY IN HINGLISH (Hindi language written in the English alphabet).
        """
    else:
        language_instruction = "CRITICAL RULE: WRITE THE ENTIRE STORY IN ENGLISH."

    system_prompt = "You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller."

    user_prompt = f"""
    Write a highly personalized, emotional bedtime story for your {age}-year-old {gender} grandchild named {child_name}.
    Core Moral to teach: "{moral_value}".
    Native Place: "{native_place}".
    {language_instruction}
    RULES: Add cultural depth. Tone must match a {age}-year-old. Add a warm grandparent greeting. Relatable struggle before doing the right thing. End with a real-world task. Length: 350-400 words.
    """
    
    try:
        # 1. TEXT GENERATION (Groq Llama-3)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
        )
        story_text = response.choices[0].message.content
        
        # 2. 100% FREE AUDIO GENERATION (Google TTS)
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
                print(audio_error)

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
