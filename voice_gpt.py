import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import tempfile
import io
import requests
import os
from pydub import AudioSegment

st.set_page_config(page_title="Azure Voice Translator", layout="centered")

# --- Secrets Loading ---
try:
    AZ_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
    AZ_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]
    AZ_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
    AZ_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]
except KeyError as e:
    st.error(f"Missing Secret: {e}. Please add it to Streamlit Secrets.")
    st.stop()

# --- Core Functions ---
def speech_to_text_auto(audio_path):
    speech_config = speechsdk.SpeechConfig(subscription=AZ_SPEECH_KEY, region=AZ_SPEECH_REGION)
    
    # LIMIT: Only 4 languages allowed for at-start detection
    auto_detect = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=["hi-IN", "kn-IN", "ta-IN", "en-IN"]
    )
    
    audio_config = speechsdk.AudioConfig(filename=audio_path)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, 
        audio_config=audio_config, 
        auto_detect_source_language_config=auto_detect
    )

    result = recognizer.recognize_once()
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        lang = speechsdk.AutoDetectSourceLanguageResult(result).language
        return result.text, lang
    return None, "unknown"

def translate_to_english(text):
    url = f"https://api.cognitive.microsofttranslator.com"
    headers = {
        "Ocp-Apim-Subscription-Key": AZ_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZ_TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=[{"text": text}])
    return response.json()[0]["translations"][0]["text"]

# --- UI Logic ---
st.title("🎙️ Indian Language → English")
audio_data = st.audio_input("Record your voice")

if audio_data:
    if st.button("Translate"):
        # 1. FIX: Transcode to 16kHz, 16-bit, Mono WAV
        with st.spinner("Processing audio..."):
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data.read()))
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                audio_segment.export(tmp.name, format="wav")
                temp_wav = tmp.name

        # 2. Transcribe
        with st.spinner("Azure is listening..."):
            text, lang = speech_to_text_auto(temp_wav)

        if text:
            st.success(f"Detected: {lang}")
            st.write(f"**Original:** {text}")
            
            # 3. Translate
            translation = translate_to_english(text)
            st.subheader("English Translation")
            st.success(translation)
        else:
            st.error("Azure couldn't detect speech. Check if your recording actually has sound.")
        
        # Cleanup
        if os.path.exists(temp_wav): os.remove(temp_wav)
