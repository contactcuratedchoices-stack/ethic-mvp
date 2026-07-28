from flask import Flask, render_template, request, jsonify
from groq import Groq
import os

app = Flask(__name__)

# API Key Render के Environment Variables से आएगी (Security First)
API_KEY = os.getenv("GROQ_API_KEY") 
client = Groq(api_key=API_KEY)

# होमपेज रेंडर करने के लिए
@app.route('/')
def home():
    return render_template('index.html')

# यह फंक्शन वेबसाइट से डेटा लेगा और हाइपर-पर्सनलाइज्ड कहानी बनाएगा
@app.route('/generate_story', methods=['POST'])
def generate_story():
    data = request.json
    child_name = data.get('child_name')
    native_place = data.get('native_place')
    age = data.get('age')
    gender = data.get('gender')
    moral_value = data.get('moral_value')
    language = data.get('language')
    
    # 🌟 THE HYPER-PERSONALIZED MASTER PROMPT 🌟
    prompt = f"""
    You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller deeply rooted in the culture of {native_place}, India. 
    Write a highly personalized, emotional bedtime story for your {age}-year-old {gender} grandchild named {child_name}.
    
    Core Moral to teach: "{moral_value}".
    Story Language: STRICTLY write the entire story in {language}. 
    (Note: If Language is 'Hinglish', write Hindi words using English alphabets. If 'Hindi', use Devanagari script. If 'English', use English but with Indian cultural terms).

    DYNAMIC ADAPTATION RULES:
    1. Cultural & Ancestral Roots (Crucial): The story MUST be set in or heavily inspired by the regional landscape, local folklore, traditional vibe, or positive local myths/Lok-Devta culture of "{native_place}". Make the parents feel nostalgic about their roots. Include sensory details (regional food, terrain, local festivals).
    2. Age-Specific Tone: Since the child is {age} years old, adapt the vocabulary, complexity, and danger-level perfectly for this age. (e.g., 3-5 yrs: cute animals, simple magic; 6-8 yrs: village adventures, bravery; 9-10 yrs: complex moral choices, ancient regional heroes).
    3. The Dadi/Nani Vibe: Start the story with a warm, nostalgic grandparent tone (e.g., "Come here, my little {child_name}, let me tell you a story from our village...").
    4. The Relatable Struggle: {child_name} MUST be the main character and face a difficult choice or temptation related to "{moral_value}".
    5. Length & Structure: Around 350-400 words. Break it into 4 engaging paragraphs.
    6. The "ETHIC" Quest: End the story with a highly specific, fun real-world task for {child_name} to do tomorrow to practice {moral_value}, framed as a secret mission from their grandparent.
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
