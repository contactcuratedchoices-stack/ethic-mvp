from flask import Flask, render_template, request, jsonify
from groq import Groq
import os

app = Flask(__name__)

# API Key Render के Environment Variables से आएगी
API_KEY = os.getenv("GROQ_API_KEY") 
client = Groq(api_key=API_KEY)

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
    
    # 🚨 THE BRAHMASTRA: Strict Language Lock using Python Logic 🚨
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

    # 🌟 SYSTEM PROMPT: Setting the Role
    system_prompt = "You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller."

    # 🌟 USER PROMPT: Giving the specifics
    user_prompt = f"""
    Write a highly personalized, emotional bedtime story for your {age}-year-old {gender} grandchild named {child_name}.
    Core Moral to teach: "{moral_value}".
    Native Place / Cultural Roots: "{native_place}".

    {language_instruction}

    STORY WRITING RULES (DO NOT IGNORE):
    1. Cultural Depth: Set the story completely in the regional landscape, local folklore, or positive local myths of "{native_place}". Make parents nostalgic (include regional food, geography, or festivals of that specific place).
    2. Age-Specific Tone: Perfectly adapt the complexity and tone for a {age}-year-old child. 
    3. The Dadi/Nani Vibe: Start the story with a warm, nostalgic grandparent greeting.
    4. The Relatable Struggle: {child_name} MUST face a difficult choice or temptation related to "{moral_value}" before doing the right thing.
    5. The "ETHIC" Quest: End the story with a highly specific, fun real-world task for {child_name} to do tomorrow to practice {moral_value}. Formulate it as a secret mission from their grandparent.
    6. Length & Quality: Write exactly 350 to 450 words. Do not summarize, do not cut the story short, and ensure perfect grammar and smooth flow.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
        )
        story = response.choices[0].message.content
        return jsonify({"success": True, "story": story})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
