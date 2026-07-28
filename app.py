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

# यह फंक्शन वेबसाइट से डेटा लेगा और बिना कामचोरी के परफेक्ट कहानी बनाएगा
@app.route('/generate_story', methods=['POST'])
def generate_story():
    data = request.json
    child_name = data.get('child_name')
    native_place = data.get('native_place')
    age = data.get('age')
    gender = data.get('gender')
    moral_value = data.get('moral_value')
    language = data.get('language')
    
    # 🌟 THE ANTI-LAZY, NATIVE-SPEAKER MASTER PROMPT 🌟
    prompt = f"""
    You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller deeply rooted in the culture of {native_place}, India. 
    Write a highly personalized, emotional bedtime story for your {age}-year-old {gender} grandchild named {child_name}.
    
    Core Moral to teach: "{moral_value}".

    CRITICAL LANGUAGE & WRITING RULES (STRICTLY FOLLOW THIS):
    1. Language Mastery: The entire story MUST be written in {language}. 
       - If {language} is 'Hindi': DO NOT translate from English word-by-word. Think and write natively in pure, grammatically perfect Hindi (Devanagari script). Ensure excellent vocabulary, complete sentences, and smooth flow. Do not skip any words or leave sentences incomplete.
       - If {language} is 'Hinglish': Write natural, conversational Indian language using the English alphabet (e.g., "Ek baar ki baat hai, ek chhota bacha tha...").
       - If {language} is 'English': Write in English but weave in Indian cultural terms and warmth seamlessly.
    
    2. No Laziness / Full Story: You MUST write a complete, detailed story of EXACTLY 350 to 450 words. Do not summarize. Do not cut the story short. 

    STORY STRUCTURE & ADAPTATION:
    3. Cultural Roots: Set the story completely in the regional landscape, local folklore, or positive local myths of "{native_place}". Make parents nostalgic (include regional food, geography, or festivals).
    4. Age-Specific Tone: Perfectly adapt the complexity and tone for a {age}-year-old child.
    5. The Dadi/Nani Vibe: Start the story with a warm, nostalgic grandparent greeting in {language}.
    6. The Relatable Struggle: {child_name} MUST face a difficult choice or temptation related to "{moral_value}" before doing the right thing.
    7. The "ETHIC" Quest: End the story with a highly specific, fun real-world task for {child_name} to do tomorrow to practice {moral_value}, framed as a secret mission from their grandparent.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        story = response.choices[0].message.content
        return jsonify({"success": True, "story": story})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
