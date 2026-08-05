from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from groq import Groq
import os
import base64
import wave
import io
import urllib.parse
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

    regional_base = RegionalStory.query.filter_by(state=native_place, moral=moral_value, theme=theme, target_gender=gender).first()
    if not regional_base:
        regional_base = RegionalStory.query.filter_by(state=native_place, moral=moral_value, target_gender=gender).first()
    if not regional_base:
        regional_base = RegionalStory.query.filter_by(state=native_place, moral=moral_value).first()
    
    regional_context = ""
    if regional_base:
        regional_context = f"""
        CRITICAL INSTRUCTION: I am providing you an authentic regional folktale from {native_place}. 
        You MUST base your entire response strictly on this story: '{regional_base.core_story}'.
        Do not invent a completely new plot, BUT you must adapt and bend this core story to perfectly fit the requested '{theme}' theme and make the main character a '{gender}'.
        """
    else:
        regional_context = f"Invent a culturally accurate folktale from {native_place} teaching {moral_value}."

    gender_role = "heroine (like a brave princess, smart girl, or fairy)" if gender == "Girl" else "hero (like a brave prince, smart boy, or warrior)"
    
    system_prompt = "You are an expert, affectionate Indian Grandparent (Dadi/Nani) and a master storyteller."
    
    user_prompt = f"""
    Write a highly personalized, emotional bedtime story.
    
    🎯 CHILD'S PROFILE: 
    - Name: {child_name}
    - Age: {age} years old
    - Gender: {gender}. Make {child_name} the main {gender_role} of the story!
    
    ✨ STORY SETTINGS:
    - Theme: "{theme}". The story MUST heavily revolve around this theme.
    - Core Moral to teach: "{moral_value}". 
    - Native Place: "{native_place}".
    
    {language_instruction}
    {regional_context}
    
    RULES: 
    1. Add cultural depth from {native_place}. 
    2. Tone must perfectly match a {age}-year-old. 
    3. Add a warm grandparent greeting. 
    4. End with a real-world task. 
    5. Length: 350-400 words.
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
        
        # 🚀 100% WORKING AI IMAGE LOGIC (Anti-Bot & Fast Gen)
        # Ek short aur perfect prompt
        image_prompt = f"Magical bedtime story illustration, {theme}, cute {age} year old Indian {gender} in {native_place}, 3D Pixar Disney animated style, masterpiece, glowing cinematic lighting"
        encoded_prompt = urllib.parse.quote(image_prompt)
        
        # Thoda chhota size (1024x768) taaki turant generate ho aur timeout na ho
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true"
        
        final_image_data = None
        try:
            # 🚀 JUGAD: Python ko Google Chrome ka roop de diya!
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            # Timeout bada kar 25 second kar diya
            img_response = requests.get(pollinations_url, headers=headers, timeout=25)
            
            if img_response.status_code == 200:
                img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                final_image_data = f"data:image/jpeg;base64,{img_base64}"
            else:
                print(f"AI Image Error: {img_response.status_code}")
                
        except Exception as e:
            print(f"AI Image Generation Failed: {e}")

        # Ab Base64 image data ko database me save karenge
        new_story = Story(user_id=session['user_id'], title=title, content=story_text, moral=moral_value, image_url=final_image_data)
        db.session.add(new_story)
        db.session.commit()
        
        audio_error = None
        
        if wants_audio:
            try:
                speech_key = os.environ.get('AZURE_SPEECH_KEY')
                service_region = os.environ.get('AZURE_SPEECH_REGION')
                
                if not speech_key or not service_region:
                    audio_error = "Azure keys not found in environment."
                else:
                    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
                    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm)
                    
                    if language == 'English':
                        voice_name = "en-IN-NeerjaNeural"
                    else:
                        voice_name = "hi-IN-AartiNeural"

                    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
                    
                    paragraphs = [p.strip() for p in story_text.split('\n') if p.strip()]
                    combined_pcm_bytes = b""
                    
                    for index, para in enumerate(paragraphs):
                        formatted_para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        
                        ssml_string = f"""
                        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="hi-IN">
                            <voice name="{voice_name}">
                                <prosody rate="0.95" pitch="medium">
                                    {formatted_para}
                                    <break time="800ms"/>
                                </prosody>
                            </voice>
                        </speak>
                        """
                        
                        result = synthesizer.speak_ssml_async(ssml_string).get()
                        
                        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                            combined_pcm_bytes += result.audio_data
                        else:
                            print(f"Warning: Chunk {index} failed with reason: {result.reason}")
                    
                    if combined_pcm_bytes:
                        wav_io = io.BytesIO()
                        with wave.open(wav_io, 'wb') as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(16000)
                            wav_file.writeframes(combined_pcm_bytes)
                        
                        audio_base64 = base64.b64encode(wav_io.getvalue()).decode('utf-8')
                        new_story.audio_data = audio_base64
                        db.session.commit()
                    else:
                        audio_error = "TTS Error: Audio could not be generated."

            except Exception as e:
                audio_error = f"Audio Generation Failed: {str(e)}"

        return jsonify({
            "success": True, 
            "story_id": new_story.id,
            "audio_error": audio_error
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
