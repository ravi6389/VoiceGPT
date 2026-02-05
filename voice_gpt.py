import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import tempfile
import requests
import json

st.set_page_config(page_title="Azure Auto-Detect Voice Translator", layout="centered")

st.title("🎙️ Auto-Detect Voice → English Translator (Azure Speech SDK)")

# -----------------------------
# Load Azure Keys
# -----------------------------
AZ_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZ_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]

AZ_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
AZ_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]

# Azure Translator endpoint (global)
TRANSLATOR_URL = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=en"


# -----------------------------
# SPEECH SDK TRANSCRIPTION
# -----------------------------
def speech_to_text_auto(audio_path):

    # Speech config
    speech_config = speechsdk.SpeechConfig(
        subscription=AZ_SPEECH_KEY,
        region=AZ_SPEECH_REGION
    )

    # Enable multi-language auto-detection
    auto_detect = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=[
            "hi-IN","kn-IN","ta-IN","te-IN","ml-IN","mr-IN",
            "bn-IN","gu-IN","pa-IN","ur-IN",
            "en-US","en-IN","es-ES","fr-FR","de-DE"
        ]
    )

    audio_config = speechsdk.AudioConfig(filename=audio_path)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
        auto_detect_source_language_config=auto_detect
    )

    result = recognizer.recognize_once()

    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        return "", "unknown"

    # Extract detected language
    lang_result = speechsdk.AutoDetectSourceLanguageResult(result)
    detected_lang = lang_result.language

    return result.text, detected_lang


# -----------------------------
# TRANSLATION
# -----------------------------
def translate_to_english(text):
    if not text:
        return ""

    headers = {
        "Ocp-Apim-Subscription-Key": AZ_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZ_TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }

    body = [{"text": text}]

    response = requests.post(TRANSLATOR_URL, headers=headers, json=body)
    data = response.json()
    return data[0]["translations"][0]["text"]


# -----------------------------
# UI — Recording
# -----------------------------
audio = st.audio_input("🎤 Record your voice (ANY language)")

if audio:
    if st.button("Translate to English"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio.read())
            temp_audio.flush()

            with st.spinner("Transcribing with Azure Speech SDK..."):
                text, lang = speech_to_text_auto(temp_audio.name)

            st.subheader("🌐 Detected Language")
            st.success(lang)

            st.subheader("📝 Original Speech")
            st.write(text if text else "No speech detected")

            if text:
                with st.spinner("Translating to English..."):
                    eng = translate_to_english(text)

                st.subheader("🌍 English Translation")
                st.success(eng)
