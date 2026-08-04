import os
import tempfile
import azure.cognitiveservices.speech as speechsdk
from flask import Flask, request, send_file, jsonify, render_template

app = Flask(__name__)

# डिफ़ॉल्ट राउट जो तुम्हारी HTML फाइल को लोड करेगा
@app.route('/')
def home():
    return render_template('login.html') 

# नया ऑडियो जनरेट करने वाला राउट (Azure TTS)
@app.route('/api/generate-audio', methods=['POST'])
def generate_audio():
    data = request.json
    text = data.get('text')

    if not text:
        return jsonify({"error": "Text is required"}), 400

    # Render के Environment Variables से Keys लेना (सिक्योर तरीका)
    speech_key = os.environ.get('AZURE_SPEECH_KEY')
    service_region = os.environ.get('AZURE_SPEECH_REGION')

    if not speech_key or not service_region:
        return jsonify({"error": "Azure credentials not configured properly in Render"}), 500

    try:
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        # आरती की आवाज़ फिक्स कर दी गई है
        speech_config.speech_synthesis_voice_name = "hi-IN-AartiNeural"

        temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_audio_file.name)

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return send_file(temp_audio_file.name, mimetype="audio/wav")
        else:
            return jsonify({"error": "Audio generation failed", "details": str(result.reason)}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
