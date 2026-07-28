from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
import requests
import base64

app = Flask(__name__)

# --- KEYS SETUP ---
# API Keys Render से आएंगी
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# 🚨 नीचे अपनी Voice ID पेस्ट करो (Inverted commas " " के अंदर ही रखना) 🚨
VOICE_ID = "ZthnDvLLxYzM9qeFVSJe"

client = Groq(api_key=GROQ_API_KEY)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    data = request.json
    child_name = data.get('child_name')
    native_place = data.get('native_place')
    age = data.get('age')
    gender = data.get('gender')
    moral_value = data.get('moral_value')
    language = data.get('language')
    
    # Language Rules
    language_instruction = ""
    if language == "Hindi":
        language_instruction = "CRITICAL RULE: WRITE ENTIRE STORY IN PURE HINDI (DEVANAGARI SCRIPT). NO ENGLISH LETTERS."
    elif language == "Hinglish":
        language_instruction = "CRITICAL RULE: WRITE ENTIRE STORY IN HINGLISH (Hindi in English alphabet)."
    else:
        language_instruction = "CRITICAL RULE: WRITE ENTIRE STORY IN ENGLISH."

    system_prompt = "You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller."

    user_prompt = f"""
    Write a highly personalized, emotional bedtime story for your {age}-year-old {gender} grandchild named {child_name}.
    Core Moral: "{moral_value}". Native Place: "{native_place}".
    {language_instruction}
    RULES: Add cultural depth. Tone must match a {age}-year-old. Add a warm grandparent greeting. Make the child face a struggle before doing the right thing. End with a real-world task (ETHIC Quest). Length: 350-400 words.
    """
    
    try:
        # 1. Generate Story Text (Groq API)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
        )
        story = response.choices[0].message.content
        
        # 2. Generate Audio (ElevenLabs API)
        audio_base64 = None
        if ELEVENLABS_API_KEY and VOICE_ID != "YOUR_VOICE_ID_HERE":
            eleven_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }
            # 'multilingual_v2' मॉडल हिंदी और इंग्लिश दोनों एकदम परफेक्ट बोलता है
            eleven_data = {
                "text": story,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            eleven_res = requests.post(eleven_url, json=eleven_data, headers=headers)
            
            if eleven_res.status_code == 200:
                # ऑडियो को एनकोड करके फ्रंटएंड पर भेज रहे हैं
                audio_base64 = base64.b64encode(eleven_res.content).decode('utf-8')

        return jsonify({"success": True, "story": story, "audio": audio_base64})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
