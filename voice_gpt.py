# import streamlit as st
# import streamlit.components.v1 as components
# import tempfile
# import requests
# import azure.cognitiveservices.speech as speechsdk

# st.set_page_config(page_title="Voice Translator", layout="centered")

# st.title("🎙️ Voice → English Translator (Streamlit Cloud Compatible)")

# # ------------------ AZURE KEYS ------------------
# AZURE_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
# AZURE_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]

# AZURE_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
# AZURE_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]

# TRANSLATOR_ENDPOINT = (
#     "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"
# )

# # ----------------- RECORDING COMPONENT -----------------
# st.subheader("🎤 Step 1: Record your voice")

# js_code = """
# <div>
# <button id="startBtn">🎙️ Start Recording</button>
# <button id="stopBtn">⛔ Stop Recording</button>
# <p id="status"></p>
# </div>

# <script>
# let mediaRecorder;
# let audioChunks = [];

# document.getElementById("startBtn").onclick = async function() {
#     document.getElementById("status").innerHTML = "Recording...";
#     const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

#     mediaRecorder = new MediaRecorder(stream);
#     mediaRecorder.start();

#     audioChunks = [];
#     mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
# };

# document.getElementById("stopBtn").onclick = function() {
#     document.getElementById("status").innerHTML = "Processing...";
#     mediaRecorder.stop();

#     mediaRecorder.onstop = () => {
#         const blob = new Blob(audioChunks, { type: "audio/webm" });
#         const file = new File([blob], "recording.webm");

#         // Put the file inside Streamlit's uploader
#         const dataTransfer = new DataTransfer();
#         dataTransfer.items.add(file);
#         document.querySelector('input[type=file]').files = dataTransfer.files;

#         document.getElementById("status").innerHTML = "Recording saved!";
#     };
# };
# </script>
# """

# components.html(js_code, height=200)

# uploaded_audio = st.file_uploader("Your recorded audio:", type=["webm", "wav"])

# # ------------ SPEECH TO TEXT ----------------
# def transcribe_audio(path):
#     speech_config = speechsdk.SpeechConfig(
#         subscription=AZURE_SPEECH_KEY,
#         region=AZURE_SPEECH_REGION
#     )

#     auto_lang = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
#         languages=[
#             "hi-IN","ta-IN","te-IN","ml-IN","kn-IN","mr-IN",
#             "bn-IN","gu-IN","pa-IN","ur-IN","en-US"
#         ]
#     )

#     audio_config = speechsdk.AudioConfig(filename=path)

#     recognizer = speechsdk.SpeechRecognizer(
#         speech_config=speech_config,
#         audio_config=audio_config,
#         auto_detect_source_language_config=auto_lang
#     )

#     result = recognizer.recognize_once()

#     if result.reason == speechsdk.ResultReason.RecognizedSpeech:
#         return result.text

#     return "⚠ Could not transcribe."

# # ------------ TRANSLATE ----------------
# def translate_to_english(text):
#     headers = {
#         "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
#         "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
#         "Content-Type": "application/json",
#     }

#     body = [{"text": text}]

#     response = requests.post(
#         TRANSLATOR_ENDPOINT + "&to=en",
#         headers=headers,
#         json=body
#     )

#     data = response.json()
#     st.write(data)
#     return data[0]["translations"][0]["text"]


# # ------------ MAIN ACTION ----------------
# if uploaded_audio:
#     st.audio(uploaded_audio)

#     temp = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
#     temp.write(uploaded_audio.read())
#     temp.flush()

#     if st.button("📝 Transcribe & Translate"):
#         st.info("Transcribing…")

#         text = transcribe_audio(temp.name)
#         st.subheader("📝 Transcription")
#         st.write(text)

#         st.info("Translating to English…")
#         english = translate_to_english(text)

#         st.subheader("🌍 English Translation")
#         st.success(english)

# import streamlit as st

# st.set_page_config(page_title="Audio Recorder & Replay", page_icon="🎙️")

# st.title("🎙️ Cloud Microphone App")

# # Initialize session state to store audio
# if "last_audio" not in st.session_state:
#     st.session_state.last_audio = None

# # 1. Recording Widget
# audio_data = st.audio_input("Record your message")

# # If a new recording is made, save it to session state
# if audio_data:
#     st.session_state.last_audio = audio_data.read()

# # 2. Replay Section
# if st.session_state.last_audio:
#     st.write("---")
#     st.subheader("Controls")
    
#     # Standard player (shows up automatically)
#     st.write("Current Recording:")
#     st.audio(st.session_state.last_audio)
    
#     # Custom Replay Button (triggers the audio again)
#     if st.button("🔄 Replay Sound"):
#         # This re-renders the audio component specifically for playback
#         st.audio(st.session_state.last_audio, autoplay=True)
#         st.toast("Replaying...")

#     # Optional: Download Button
#     st.download_button(
#         label="📥 Download Recording",
#         data=st.session_state.last_audio,
#         file_name="cloud_recording.wav",
#         mime="audio/wav"
#     )
# else:
#     st.info("Record something above to enable the replay button.")

import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import tempfile
import os
from pydub import AudioSegment

st.title("🎙️ Auto-Detect & Translate")

# Azure Credentials
AZURE_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]

def convert_to_wav(audio_input):
    """Converts browser audio to Azure-compatible 16kHz Mono WAV"""
    audio = AudioSegment.from_file(audio_input)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        audio.export(tmp_wav.name, format="wav")
        return tmp_wav.name

def translate_audio(audio_path):
    translation_config = speechsdk.translation.SpeechTranslationConfig(
        subscription=AZURE_SPEECH_KEY, 
        region=AZURE_SPEECH_REGION
    )
    translation_config.add_target_language("en")
    
    # Supported languages
    auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=["hi-IN", "ta-IN", "te-IN", "bn-IN", "en-US", "es-ES"]
    )

    audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
    recognizer = speechsdk.translation.TranslationRecognizer(
        translation_config=translation_config,
        audio_config=audio_config,
        auto_detect_source_language_config=auto_detect_config
    )

    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.TranslatedSpeech:
        lang = result.properties.get(speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult)
        return lang, result.text, result.translations['en']
    
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        return None, None, f"Error: {cancellation.reason} - {cancellation.error_details}"
    
    return None, None, "Speech not recognized."

# UI Logic
audio_value = st.audio_input("Record your voice")

if audio_value:
    if st.button("✨ Auto-Detect & Translate"):
        # Step 1: Format Conversion
        with st.spinner("Processing audio format..."):
            fixed_wav_path = convert_to_wav(audio_value)
        
        # Step 2: Azure Translation
        lang, original, translated = translate_audio(fixed_wav_path)
        
        if lang:
            st.success(f"Detected: {lang}")
            st.write(f"**Original:** {original}")
            st.info(f"**English:** {translated}")
        else:
            st.error(translated)
            
        # Cleanup
        if os.path.exists(fixed_wav_path):
            os.remove(fixed_wav_path)
