from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from groq import Groq
import os
import base64
import wave
import io
import json
import urllib.parse
import random
import requests
import azure.cognitiveservices.speech as speechsdk
from extensions import db
from models import Child, Story, RegionalStory

main_bp = Blueprint('main', __name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
client = Groq(api_key=GROQ_API_KEY)

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to view your dashboard.', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user_children = Child.query.filter_by(user_id=user_id).all()
    user_stories = Story.query.filter_by(user_id=user_id).order_by(Story.created_at.desc()).all()
    
    return render_template('dashboard.html', children=user_children, stories=user_stories)

@main_bp.route('/studio')
def studio():
    if 'user_id' not in session:
        flash('Please log in or create an account to generate your first story.', 'error')
        return redirect(url_for('auth.login'))
    
    user_children = Child.query.filter_by(user_id=session['user_id']).all()
    return render_template('studio.html', children=user_children)

@main_bp.route('/story/<int:story_id>')
def read_story(story_id):
    if 'user_id' not in session:
        flash('Please log in to read stories.', 'error')
        return redirect(url_for('auth.login'))
    
    story = Story.query.get_or_404(story_id)
    if story.user_id != session['user_id'] and not session.get('is_admin'):
        flash('Unauthorized access!', 'error')
        return redirect(url_for('main.dashboard'))
        
    return render_template('read_story.html', story=story)

@main_bp.route('/add_child', methods=['POST'])
def add_child():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    name = request.form.get('child_name')
    age = request.form.get('age')
    native_place = request.form.get('native_place')
    language = request.form.get('language')
    gender = request.form.get('gender', 'Any') 
    
    new_child = Child(user_id=session['user_id'], name=name, age=age, native_place=native_place, language=language, gender=gender)
    db.session.add(new_child)
    db.session.commit()
    
    flash(f'{name} profile added successfully!', 'success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/generate_story', methods=['POST'])
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
    gender = data.get('gender', 'Boy')
    theme = data.get('theme', 'General')
    
    language_instruction = ""
    if language == "Hindi":
        language_instruction = "CRITICAL RULE: YOU MUST WRITE THE ENTIRE STORY STRICTLY IN PURE HINDI USING THE DEVANAGARI SCRIPT."
    elif language == "Hinglish":
        language_instruction = "CRITICAL RULE: WRITE THE ENTIRE STORY IN HINGLISH."
    else:
        language_instruction = "CRITICAL RULE: WRITE THE ENTIRE STORY IN ENGLISH."

    # 🚀 NEW: Fetching Regional Data properly with the new CMS Architecture
    regional_base = RegionalStory.query.filter_by(state=native_place, moral=moral_value, theme=theme, target_gender=gender).first()
    if not regional_base:
        regional_base = RegionalStory.query.filter_by(state=native_place, moral=moral_value, target_gender=gender).first()
    if not regional_base:
        regional_base = RegionalStory.query.filter_by(state=native_place, moral=moral_value).first()
    
    regional_context = ""
    if regional_base:
        regional_context = f"""
        CRITICAL INSTRUCTION: I am providing you an authentic regional folktale from {native_place} (Specific Region: {regional_base.region}). 
        You MUST base your entire response strictly on this core story: '{regional_base.core_story}'.
        The Deep Specific Moral/Lesson to subtly teach is: '{regional_base.specific_moral}'.
        Do not invent a completely new plot, BUT you must adapt and bend this core story to perfectly fit the requested '{theme}' theme and make the main character a '{gender}'.
        """
    else:
        regional_context = f"Invent a culturally accurate folktale from {native_place} teaching {moral_value}."

    gender_role = "heroine (like a brave princess, smart girl, or fairy)" if gender == "Girl" else "hero (like a brave prince, smart boy, or warrior)"
    
    # 🚀 NEW: Enforcing JSON Format for Interactivity
    system_prompt = """You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller.
    You MUST output your response STRICTLY as a JSON object. Do not include any markdown formatting or extra text.
    The JSON must contain exactly these two keys:
    1. "story_text": The complete, engaging bedtime story.
    2. "interactive_question": A single, exciting question asked at the very end to let the child choose what the hero should do next."""
    
    user_prompt = f"""
    Write a highly personalized, emotional bedtime story.
    
    🎯 CHILD'S PROFILE: 
    - Name: {child_name}
    - Age: {age} years old
    - Gender: {gender}. Make {child_name} the main {gender_role} of the story!
    
    ✨ STORY SETTINGS:
    - Theme: "{theme}". The story MUST heavily revolve around this theme.
    - Native Place: "{native_place}".
    
    {language_instruction}
    {regional_context}
    
    RULES: 
    1. Add cultural depth from {native_place}. 
    2. Tone must perfectly match a {age}-year-old. 
    3. Add a warm grandparent greeting. 
    4. Length: 350-400 words.
    5. Ensure the 'interactive_question' leaves the story on a cliffhanger.
    """
    
    try:
        # 🚀 FIX: Using a stable Groq model and enforcing JSON mode
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama3-8b-8192", 
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        # 🚀 NEW: Parsing the JSON response
        raw_content = response.choices[0].message.content
        parsed_data = json.loads(raw_content)
        
        story_text = parsed_data.get("story_text", "")
        interactive_question = parsed_data.get("interactive_question", "")
        
        # Combine text for the database and UI
        full_content = story_text + "\n\n" + interactive_question
        title = f"{child_name}'s Tale of {moral_value}"
        
        # 🚀 REMOVED: Video/Image generation completely deleted for speed and focus.
        # We use a default ambient background image so the DB doesn't throw errors.
        cover_image_url = "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=2094&auto=format&fit=crop"

        new_story = Story(user_id=session['user_id'], title=title, content=full_content, moral=moral_value, image_url=cover_image_url)
        db.session.add(new_story)
        db.session.commit()
        
        audio_error = None
        if wants_audio:
            try:
                speech_key = os.environ.get('AZURE_SPEECH_KEY')
                service_region = os.environ.get('AZURE_SPEECH_REGION')
                
                if speech_key and service_region:
                    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
                    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm)
                    
                    # 🚀 INTACT: Azure Voice Configuration (Untouched as requested)
                    voice_name = "en-IN-NeerjaNeural" if language == 'English' else "hi-IN-SwaraNeural"
                    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
                    
                    # We will synthesize the story, and add the interactive question at the end!
                    paragraphs = [p.strip() for p in story_text.split('\n') if p.strip()]
                    if interactive_question:
                        paragraphs.append(interactive_question.strip())
                        
                    combined_pcm_bytes = b""
                    
                    for para in paragraphs:
                        formatted_para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        
                        formatted_para = formatted_para.replace('.', '. <break time="800ms"/>')
                        formatted_para = formatted_para.replace(',', ', <break time="400ms"/>')
                        formatted_para = formatted_para.replace('!', '! <break time="600ms"/>')
                        
                        ssml_string = f"""
                        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="hi-IN">
                            <voice name="{voice_name}">
                                <prosody rate="0.85" pitch="-2%">
                                    {formatted_para}
                                </prosody>
                                <break time="1500ms"/>
                            </voice>
                        </speak>
                        """
                        result = synthesizer.speak_ssml_async(ssml_string).get()
                        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                            combined_pcm_bytes += result.audio_data
                    
                    if combined_pcm_bytes:
                        wav_io = io.BytesIO()
                        with wave.open(wav_io, 'wb') as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(16000)
                            wav_file.writeframes(combined_pcm_bytes)
                        new_story.audio_data = base64.b64encode(wav_io.getvalue()).decode('utf-8')
                        db.session.commit()
            except Exception as e:
                audio_error = str(e)

        return jsonify({"success": True, "story_id": new_story.id, "audio_error": audio_error})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
