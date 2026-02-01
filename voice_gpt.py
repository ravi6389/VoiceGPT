import streamlit as st
from audiorecorder import audiorecorder
import numpy as np
import scipy.io.wavfile as wav
import azure.cognitiveservices.speech as speechsdk
import requests


# Read Azure keys from Streamlit secrets
AZURE_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]

AZURE_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
AZURE_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]

TRANSLATOR_ENDPOINT = (
    "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"
)

# UI setup
st.set_page_config(page_title="Voice → English Translator", layout="centered")
st.title("🎙️ Voice → English Translator")

if "recorded_file" not in st.session_state:
    st.session_state.recorded_file = None


# -------------------------------------------------------------
# RECORD AUDIO USING BROWSER MICROPHONE
# -------------------------------------------------------------
def record_audio():
    st.info("🎤 Click 'Start Recording' and speak...")

    audio = audiorecorder("Start Recording", "Stop Recording")

    if len(audio) > 0:
        st.success("Recording completed!")
        st.audio(audio.tobytes(), format="audio/wav")

        # Convert to numpy array
        audio_bytes = audio.tobytes()
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

        # Save WAV file
        wav.write("audio.wav", 16000, audio_np)
        st.session_state.recorded_file = "audio.wav"


# -------------------------------------------------------------
# SPEECH → TEXT (Azure)
# -------------------------------------------------------------
def transcribe_audio():
    if not st.session_state.recorded_file:
        st.error("Please record audio first!")
        return ""

    st.info("Transcribing with Azure Speech…")

    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION
    )

    auto_detect = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=[
            "hi-IN", "ta-IN", "te-IN", "ml-IN", "kn-IN",
            "mr-IN", "bn-IN", "gu-IN", "pa-IN", "ur-IN",
            "en-US", "es-ES"
        ]
    )

    audio_config = speechsdk.AudioConfig(filename=st.session_state.recorded_file)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
        auto_detect_source_language_config=auto_detect
    )

    result = recognizer.recognize_once()

    st.write("DEBUG: Result Reason:", result.reason)
    st.write("DEBUG: Text:", result.text)

    # Handle cancellation errors properly
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = speechsdk.CancellationDetails(result)
        st.error("Azure Speech FAILED")

        st.write("Cancel Reason:", cancellation.reason)
        st.write("Error Code:", cancellation.error_code)
        st.write("Details:", cancellation.error_details)
        return ""

    return result.text


# -------------------------------------------------------------
# TRANSLATION → ENGLISH
# -------------------------------------------------------------
def translate_to_english(text):
    if not text:
        return "No transcription available."

    st.info("Translating to English…")

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json",
    }

    body = [{"text": text}]

    response = requests.post(
        TRANSLATOR_ENDPOINT + "&to=en",
        headers=headers,
        json=body
    )

    data = response.json()
    return data[0]["translations"][0]["text"]


# -------------------------------------------------------------
# UI
# -------------------------------------------------------------
st.subheader("🎤 Step 1: Record your voice")

record_audio()

if st.button("📝 Transcribe & Translate"):
    if st.session_state.recorded_file:
        st.audio(st.session_state.recorded_file)

    text = transcribe_audio()

    st.markdown("### 📝 Transcription")
    st.write(text)

    english = translate_to_english(text)

    st.markdown("### 🌍 English Translation")
    st.success(english)

