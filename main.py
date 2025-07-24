from flask import Flask, render_template, request, jsonify
import os
from google import genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from PIL import Image
import speech_recognition as sr
import pyaudio

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the Google Gemini API client
api_key = os.getenv('GOOGLE_API_KEY')  # your Google API key from .env
client = genai.Client(api_key=api_key)

# Initialize speech recognizer
r = sr.Recognizer()

# Chat history to display on UI
history = []

@app.route('/')
def home():
    return render_template('index.html', history=history)

@app.route('/generate', methods=['POST'])
def generate_content():
    content = request.form.get('content')
    response = client.models.generate_content(model="gemini-2.5-flash", contents=content)
    history.append({'type': 'text', 'input': content, 'response': response.text})
    return jsonify({'text': response.text})

@app.route('/upload', methods=['POST'])
def upload_image():
    image = request.files['image']
    filename = secure_filename(image.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)

    image_pil = Image.open(filepath)
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[image_pil, "Tell me about this image."])
        analysis_text = response.text
    except Exception as e:
        analysis_text = f"Error during analysis: {str(e)}"

    history.append({'type': 'image', 'input': filename, 'response': analysis_text})
    return render_template('index.html', history=history, image_url=filename, analysis=analysis_text)

@app.route('/listen', methods=['POST'])
def listen():
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)
        r.pause_threshold = 1
        print("Listening...")

        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            query = r.recognize_google(audio, language="en-in")
            print(f"You said: {query}")
            response = client.models.generate_content(model="gemini-2.5-flash", contents=query)
            history.append({'type': 'voice', 'input': query, 'response': response.text})
            return jsonify({'text': response.text})
        except Exception as e:
            return jsonify({'text': "Sorry, I couldn't understand the audio. Please try again."})

if __name__ == '__main__':
    app.run(debug=True)


