from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
import requests
import base64

app = Flask(__name__)

# API Keys Render के Environment Variables से ली जाएंगी
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# 🚨🚨🚨 यहाँ अपनी ElevenLabs की VOICE ID डालें (API Key नहीं) 🚨🚨🚨
VOICE_ID = "jBpfuIE2acCO8z3wKNLl" 

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
    
    wants_audio = data.get('generate_audio', False)
    
    # 🚨 THE BRAHMASTRA: Strict Language Lock
    language_instruction = ""
    if language == "Hindi":
        language_instruction = """
        CRITICAL RULE: YOU MUST WRITE THE ENTIRE STORY STRICTLY IN PURE HINDI USING THE DEVANAGARI SCRIPT (हिंदी लिपि). 
        DO NOT USE ENGLISH LETTERS FOR HINDI. 
        Example of correct format: 'एक बार की बात है, एक बहुत ही प्यारा बच्चा था...'
        Do not output Romanized Hindi or Hinglish.
        """
    elif language == "Hinglish":
        language_instruction = """
        CRITICAL RULE: WRITE THE ENTIRE STORY IN HINGLISH (Hindi language written in the English alphabet).
        Example of correct format: 'Ek baar ki baat hai, ek bahut hi pyara bacha tha...'
        """
    else:
        language_instruction = "CRITICAL RULE: WRITE THE ENTIRE STORY IN ENGLISH."

    system_prompt = "You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller."

    user_prompt = f"""
    Write a highly personalized, emotional bedtime story for your {age}-year-old {gender} grandchild named {child_name}.
    Core Moral to teach: "{moral_value}".
    Native Place / Cultural Roots: "{native_place}".

    {language_instruction}

    STORY WRITING RULES (DO NOT IGNORE):
    1. Cultural Depth: Set the story completely in the regional landscape, local folklore, or positive local myths of "{native_place}". Make parents nostalgic.
    2. Age-Specific Tone: Perfectly adapt the complexity and tone for a {age}-year-old child. 
    3. The Dadi/Nani Vibe: Start the story with a warm, nostalgic grandparent greeting.
    4. The Relatable Struggle: {child_name} MUST face a difficult choice or temptation related to "{moral_value}" before doing the right thing.
    5. The "ETHIC" Quest: End the story with a highly specific, fun real-world task for {child_name} to do tomorrow to practice {moral_value}. Formulate it as a secret mission.
    6. Length & Quality: Write exactly 350 to 450 words. Do not summarize, do not cut the story short, and ensure perfect grammar and smooth flow.
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
        
        # 2. AUDIO GENERATION (ElevenLabs) 
        audio_base64 = None
        audio_error = None  # 🌟 NEW: Error capturing variable
        
        if wants_audio:
            if not ELEVENLABS_API_KEY or VOICE_ID == "YOUR_VOICE_ID_HERE":
                audio_error = "API Key or Voice ID is missing in app.py / Render Environment."
            else:
                eleven_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": ELEVENLABS_API_KEY
                }
                eleven_data = {
                    "text": story_text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True
                    }
                }
                
                eleven_res = requests.post(eleven_url, json=eleven_data, headers=headers)
                
                if eleven_res.status_code == 200:
                    audio_base64 = base64.b64encode(eleven_res.content).decode('utf-8')
                else:
                    audio_error = f"ElevenLabs API Error (Code: {eleven_res.status_code}): {eleven_res.text}"
                    print(audio_error)

        return jsonify({
            "success": True, 
            "story": story_text, 
            "audio_base64": audio_base64,
            "audio_error": audio_error  # Sending error to frontend
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
