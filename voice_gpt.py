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

# import streamlit as st
# import requests
# import tempfile
# import os
# from pydub import AudioSegment

# st.title("🎙️ UK West Voice Translator")

# # Load Secrets
# AZ_KEY = st.secrets["AZURE_SPEECH_KEY"]
# AZ_REGION = st.secrets["AZURE_SPEECH_REGION"] # "ukwest"
# TRANS_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]

# def transcribe_and_translate(audio_file):
#     # 1. AUDIO CONVERSION (Required for Azure REST)
#     audio = AudioSegment.from_file(audio_file)
#     audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
#         audio.export(tmp.name, format="wav")
#         with open(tmp.name, "rb") as f:
#             raw_data = f.read()

#     # 2. SPEECH-TO-TEXT (STT) - Fixed URL Construction
#     # We combine the region with the official microsoft domain
#     stt_endpoint = f"https://{AZ_REGION}://"
    
#     stt_headers = {
#         "Ocp-Apim-Subscription-Key": AZ_KEY,
#         "Content-type": "audio/wav; codec=audio/pcm; samplerate=16000",
#         "Accept": "application/json"
#     }

#     try:
#         # Get Transcription
#         stt_response = requests.post(stt_endpoint, headers=stt_headers, data=raw_data)
#         stt_response.raise_for_status()
#         transcription = stt_response.json().get("DisplayText", "")

#         if not transcription:
#             return "No speech detected.", ""

#         # 3. TRANSLATION - Fixed URL Construction
#         trans_endpoint = "https://api.cognitive.microsofttranslator.com"
        
#         trans_headers = {
#             "Ocp-Apim-Subscription-Key": TRANS_KEY,
#             "Ocp-Apim-Subscription-Region": AZ_REGION, # Required for regional keys
#             "Content-type": "application/json"
#         }
        
#         body = [{"text": transcription}]
#         trans_response = requests.post(trans_endpoint, headers=trans_headers, json=body)
#         trans_response.raise_for_status()
        
#         translation = trans_response.json()[0]["translations"][0]["text"]
#         return transcription, translation

#     except Exception as e:
#         return f"Error: {str(e)}", ""
#     finally:
#         if os.path.exists(tmp.name):
#             os.remove(tmp.name)

# # --- UI ---
# audio_input = st.audio_input("Record your voice (Hindi)")

# if audio_input:
#     if st.button("Translate to English"):
#         with st.spinner("Processing..."):
#             orig, trans = transcribe_and_translate(audio_input)
            
#             if trans:
#                 st.write(f"**Original:** {orig}")
#                 st.success(f"**English:** {trans}")
#             else:
#                 st.error(orig)
import streamlit as st
import requests
import uuid
import tempfile
from pydub import AudioSegment

st.title("🎙️ REST-Only Voice Translator")

# Secrets
AZ_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZ_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]
AZ_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
AZ_TRANSLATOR_ENDPOINT = st.secrets.get("AZ_TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com")

def transcribe_and_translate_rest(audio_file):
    try:
        # 1️⃣ Process Audio for REST (Must be WAV 16k mono)
        audio = AudioSegment.from_file(audio_file)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            audio.export(tmp.name, format="wav")
            wav_bytes = open(tmp.name, "rb").read()

        # 2️⃣ Speech-to-Text REST
        # Note: REST requires a 'language' param. For India, hi-IN is a safe broad base.
        stt_url = (
    f"https://{AZ_SPEECH_REGION}.stt.speech.microsoft.com/"
    "speech/recognition/conversation/cognitiveservices/v1"
    "?language=hi-IN"
)

        st.write('stt_url is...', stt_url)
        stt_headers = {
            "Ocp-Apim-Subscription-Key": AZ_SPEECH_KEY,
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json",
        }
        st.write('stt_headers are...', stt_headers)

        trans_url = (
    "https://api.cognitive.microsofttranslator.com"
    "?api-version=3.0&to=en"
)
        st.write('trans_url is...', trans_url)
        stt_response = requests.post(stt_url, headers=stt_headers, data=wav_bytes)
        st.write(stt_response)
        if stt_response.status_code != 200:
            return f"STT Error: {stt_response.text}", ""

        original_text = stt_response.json().get("DisplayText", "")
        if not original_text:
            return "No speech detected.", ""

        # 3️⃣ Translator REST (AUTO-DETECT enabled here)
        # By removing the '&from=' parameter, Azure Translator auto-detects the text language

        trans_headers = {
            "Ocp-Apim-Subscription-Key": AZ_TRANSLATOR_KEY,
            "Ocp-Apim-Subscription-Region": AZ_SPEECH_REGION,
            "Content-Type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4())
        }

        body = [{"text": original_text}]
        t_response = requests.post(trans_url, headers=trans_headers, json=body)
        
        if t_response.status_code != 200:
            return f"Translation Error: {t_response.text}", ""
            
        translation = t_response.json()[0]["translations"][0]["text"]

        return original_text, translation

    except Exception as e:
        return f"Error: {str(e)}", ""

# UI Logic
audio_input = st.audio_input("Record your voice")

if audio_input:
    if st.button("Translate"):
        with st.spinner("Processing via REST API..."):
            orig, trans = transcribe_and_translate_rest(audio_input)
            st.write(f"**Original:** {orig}")
            st.success(f"**English:** {trans}")




