from flask import Flask, render_template, request, jsonify
from groq import Groq
import os

app = Flask(__name__)

# अब हम चाबी को कोड में नहीं लिखेंगे, बल्कि सर्वर (Render) से उठाएंगे
API_KEY = os.getenv("GROQ_API_KEY") 
client = Groq(api_key=API_KEY)

# ... (बाकी का पूरा कोड नीचे वैसा ही रहेगा) ...

# यह फंक्शन तुम्हारी वेबसाइट का डिज़ाइन दिखाएगा
@app.route('/')
def home():
    return render_template('index.html')

# यह फंक्शन वेबसाइट से डेटा लेगा और कहानी बनाकर वापस भेजेगा
@app.route('/generate_story', methods=['POST'])
def generate_story():
    data = request.json
    child_name = data.get('child_name')
    age = data.get('age')
    gender = data.get('gender')
    moral_value = data.get('moral_value')
    language = data.get('language')
    
    prompt = f"""
    You are an expert Indian storyteller and child psychologist. 
    Write an engaging, screen-free bedtime story for a {age}-year-old {gender} named {child_name}.
    Core Moral: "{moral_value}".
    Language: Write the story in {language}.
    Make it highly imaginative with an Indian context. Keep it around 300 words.
    End with a small "Character Quest" for the child.
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
    print("🚀 ETHIC वेबसाइट चालू हो रही है! अपने ब्राउज़र में http://127.0.0.1:5000 खोलें")
    app.run(debug=True)