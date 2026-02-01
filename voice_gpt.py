import streamlit as st
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
import azure.cognitiveservices.speech as speechsdk
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AZURE_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]

AZURE_TRANSLATOR_KEY =  st.secrets["AZURE_TRANSLATOR_KEY"]
AZURE_TRANSLATOR_REGION =  st.secrets["AZURE_TRANSLATOR_REGION"]

st.write('AZURE_SPEECH_KEY', AZURE_SPEECH_KEY)
st.write('AZURE_SPEECH_REGION', AZURE_SPEECH_REGION)

st.write('AZURE_TRANSLATOR_KEY', AZURE_TRANSLATOR_KEY)
st.write('AZURE_TRANSLATOR_REGION', AZURE_TRANSLATOR_REGION)



TRANSLATOR_ENDPOINT = (
    "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"
)

# Mic config
MIC_DEVICE_INDEX = 1     # <-- Your working microphone
SAMPLE_RATE = 16000
import azure.cognitiveservices.speech as speechsdk
st.write(speechsdk.__file__)
# UI setup
st.set_page_config(page_title="Voice → English Translator", layout="centered")
st.title("🎙️ Voice → English Translator")

if "recorded_file" not in st.session_state:
    st.session_state.recorded_file = None

# -------------------------------------------------------------
# RECORD AUDIO (Option A)
# -------------------------------------------------------------
def record_audio(duration):
    sd.default.device = (MIC_DEVICE_INDEX, None)

    st.info("🎤 Recording... speak now!")

    recording = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()

    # Save WAV
    wav.write("audio.wav", SAMPLE_RATE, recording)
    st.session_state.recorded_file = "audio.wav"

    st.success("Recording completed!")
    st.audio("audio.wav")


# -------------------------------------------------------------
# SPEECH TO TEXT
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
            "hi-IN","ta-IN","te-IN","ml-IN","kn-IN","mr-IN",
            "bn-IN","gu-IN","pa-IN","ur-IN","en-US","es-ES"
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

    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = speechsdk.CancellationDetails.from_result(result)

        st.error("Azure Speech FAILED")

        st.write("CANCEL Reason:", cancellation.reason)
        st.write("Error Code:", cancellation.error_code)
        st.write("Details:", cancellation.error_details)

        return ""


    # Handle cancellation
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = speechsdk.CancellationDetailsBase(result)
        st.error("Azure Speech FAILED")
        st.write("Cancel Reason:", cancellation.reason)
        st.write("Error Code:", cancellation.error_code)
        st.write("Details:", cancellation.error_details)
        return ""




# -------------------------------------------------------------
# TRANSLATE TEXT → ENGLISH
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
# UI: Buttons
# -------------------------------------------------------------
duration = st.slider("Recording duration (seconds):", 2, 15, 5)

if st.button("🎤 Record Audio"):
    record_audio(duration)

if st.button("📝 Transcribe & Translate"):
    st.audio(st.session_state.recorded_file)
    text = transcribe_audio()

    st.markdown("### 📝 Transcription")
    st.write(text)

    english = translate_to_english(text)

    st.markdown("### 🌍 English Translation")
    st.success(english)

