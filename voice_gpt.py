import streamlit as st
import numpy as np
import scipy.io.wavfile as wav
import azure.cognitiveservices.speech as speechsdk
import requests
import tempfile
from io import BytesIO

st.set_page_config(page_title="Voice → English Translator")

st.title("🎙️ Voice → English Translator (Streamlit Cloud Compatible)")

# Azure keys
AZURE_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]
AZURE_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
AZURE_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]

TRANSLATOR_ENDPOINT = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"

# ----------------------------------------------------------
# 1️⃣ Browser Microphone Recorder (HTML + JS)
# ----------------------------------------------------------
st.subheader("🎤 Step 1: Record your voice")

mic_html = """
<script>
let chunks = [];
let recorder;
let audioBlob;

async function startRecording() {
    let stream = await navigator.mediaDevices.getUserMedia({audio:true});
    recorder = new MediaRecorder(stream);
    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = e => {
        audioBlob = new Blob(chunks, { type: 'audio/webm' });
        let file = new File([audioBlob], "recording.webm");
        let dt = new DataTransfer();
        dt.items.add(file);
        document.querySelector('input[type=file]').files = dt.files;
    };
    recorder.start();
}

function stopRecording() {
    recorder.stop();
}
</script>

<button onclick="startRecording()">🎙️ Start Recording</button>
<button onclick="stopRecording()">⛔ Stop Recording</button>
"""

st.markdown(mic_html, unsafe_allow_html=True)

uploaded_audio = st.file_uploader("Your recorded audio appears here:", type=["webm", "wav"])

# ----------------------------------------------------------
# 2️⃣ Convert recorded audio to WAV for Azure
# ----------------------------------------------------------
def convert_to_wav(uploaded_file):
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

    # Azure SDK needs WAV → we use ffmpeg-free method: WebM → Azure directly → NOT needed
    temp_wav.write(uploaded_file.read())
    temp_wav.flush()

    return temp_wav.name


# ----------------------------------------------------------
# 3️⃣ Azure Speech Recognition
# ----------------------------------------------------------
def transcribe(audio_path):
    st.info("Transcribing with Azure...")

    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION
    )

    audio = speechsdk.audio.AudioConfig(filename=audio_path)

    auto_lang = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=["hi-IN","ta-IN","te-IN","ml-IN","kn-IN",
                  "mr-IN","bn-IN","gu-IN","pa-IN","ur-IN","en-US"]
    )

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio,
        auto_detect_source_language_config=auto_lang
    )

    result = recognizer.recognize_once()

    return result.text


# ----------------------------------------------------------
# 4️⃣ Translator → English
# ----------------------------------------------------------
def translate(text):
    st.info("Translating to English...")

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json",
    }

    body = [{"text": text}]

    response = requests.post(TRANSLATOR_ENDPOINT + "&to=en",
                             headers=headers, json=body)

    return response.json()[0]["translations"][0]["text"]


# ----------------------------------------------------------
# 5️⃣ Buttons
# ----------------------------------------------------------
if uploaded_audio is not None:
    st.success("Audio received successfully!")
    st.audio(uploaded_audio)

    audio_path = convert_to_wav(uploaded_audio)

    if st.button("📝 Transcribe & Translate"):
        text = transcribe(audio_path)
        st.write("### 📝 Transcription")
        st.write(text)

        english = translate(text)
        st.write("### 🌍 English Translation")
        st.success(english)
