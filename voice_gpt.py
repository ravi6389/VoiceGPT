# import streamlit as st
# import azure.cognitiveservices.speech as speechsdk
# import tempfile
# import requests
# import json

# st.set_page_config(page_title="Azure Auto-Detect Voice Translator", layout="centered")

# st.title("🎙️ Auto-Detect Voice → English Translator (Azure Speech SDK)")

# # -----------------------------
# # Load Azure Keys
# # -----------------------------
# AZ_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
# AZ_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]

# AZ_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
# AZ_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]

# # Azure Translator endpoint (global)
# TRANSLATOR_URL = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=en"


# # -----------------------------
# # SPEECH SDK TRANSCRIPTION
# # -----------------------------
# def speech_to_text_auto(audio_path):

#     # Speech config
#     speech_config = speechsdk.SpeechConfig(
#         subscription=AZ_SPEECH_KEY,
#         region=AZ_SPEECH_REGION
#     )

#     # Enable multi-language auto-detection
#     auto_detect = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
#         languages=[
#             "hi-IN","kn-IN","ta-IN"
#             # ,"te-IN","ml-IN","mr-IN",
#             # "bn-IN","gu-IN","pa-IN","ur-IN",
#             # "en-US","en-IN","es-ES","fr-FR","de-DE"
#         ]
#     )

#     audio_config = speechsdk.AudioConfig(filename=audio_path)

#     recognizer = speechsdk.SpeechRecognizer(
#         speech_config=speech_config,
#         audio_config=audio_config,
#         auto_detect_source_language_config=auto_detect
#     )

#     result = recognizer.recognize_once()

#     if result.reason != speechsdk.ResultReason.RecognizedSpeech:
#         return "", "unknown"

#     # Extract detected language
#     lang_result = speechsdk.AutoDetectSourceLanguageResult(result)
#     detected_lang = lang_result.language

#     return result.text, detected_lang


# # -----------------------------
# # TRANSLATION
# # -----------------------------
# def translate_to_english(text):
#     if not text:
#         return ""

#     headers = {
#         "Ocp-Apim-Subscription-Key": AZ_TRANSLATOR_KEY,
#         "Ocp-Apim-Subscription-Region": AZ_TRANSLATOR_REGION,
#         "Content-Type": "application/json"
#     }

#     body = [{"text": text}]

#     response = requests.post(TRANSLATOR_URL, headers=headers, json=body)
#     data = response.json()
#     return data[0]["translations"][0]["text"]


# # -----------------------------
# # UI — Recording
# # -----------------------------
# audio = st.audio_input("🎤 Record your voice (ANY language)")

# if audio:
#     if st.button("Translate to English"):
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
#             temp_audio.write(audio.read())
#             temp_audio.flush()

#             with st.spinner("Transcribing with Azure Speech SDK..."):
#                 text, lang = speech_to_text_auto(temp_audio.name)

#             st.subheader("🌐 Detected Language")
#             st.success(lang)

#             st.subheader("📝 Original Speech")
#             st.write(text if text else "No speech detected")

#             if text:
#                 with st.spinner("Translating to English..."):
#                     eng = translate_to_english(text)

#                 st.subheader("🌍 English Translation")
#                 st.success(eng)
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import tempfile
import io
import requests
from pydub import AudioSegment

st.set_page_config(page_title="Azure Auto-Detect Voice Translator", layout="centered")

st.title("🎙️ Indian Language → English Translator")
st.markdown("Supports **Hindi, Kannada, Tamil, and Telugu** via Azure AI.")

# 1. Load Azure Secrets from Streamlit Cloud
try:
    AZ_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
    AZ_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]
    AZ_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
    AZ_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]
except Exception as e:
    st.error("Missing Secrets! Ensure AZURE_SPEECH_KEY, etc., are set in Streamlit Settings.")
    st.stop()

# -----------------------------
# SPEECH SDK TRANSCRIPTION
# -----------------------------
def speech_to_text_auto(audio_path):
    speech_config = speechsdk.SpeechConfig(
        subscription=AZ_SPEECH_KEY,
        region=AZ_SPEECH_REGION
    )

    # Azure 'At-Start' detection is limited to 4 languages.
    # We pick the 4 most likely Indian languages for your request.
    auto_detect = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=["hi-IN", "kn-IN", "ta-IN", "te-IN"]
    )

    audio_config = speechsdk.AudioConfig(filename=audio_path)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
        auto_detect_source_language_config=auto_detect
    )

    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        lang_result = speechsdk.AutoDetectSourceLanguageResult(result)
        return result.text, lang_result.language
    else:
        return "", "unknown"

# -----------------------------
# TRANSLATION
# -----------------------------
def translate_to_english(text):
    if not text: return ""
    
    url = "https://api.cognitive.microsofttranslator.com"
    headers = {
        "Ocp-Apim-Subscription-Key": AZ_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZ_TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }
    body = [{"text": text}]
    
    response = requests.post(url, headers=headers, json=body)
    return response.json()[0]["translations"][0]["text"]

# -----------------------------
# UI & AUDIO PROCESSING
# -----------------------------
audio_data = st.audio_input("🎤 Record your voice")

if audio_data:
    if st.button("Translate to English"):
        # STEP 1: Transcode browser audio (WebM) to Azure-friendly WAV
        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data.read()))
            # Azure standard: 16kHz, 16-bit, Mono
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
                audio_segment.export(temp_wav.name, format="wav")
                temp_wav_path = temp_wav.name
        except Exception as e:
            st.error(f"Audio conversion failed: {e}")
            st.stop()

        # STEP 2: Transcribe and Detect Language
        with st.spinner("Analyzing speech and language..."):
            text, lang = speech_to_text_auto(temp_wav_path)

        # STEP 3: Display and Translate
        if lang != "unknown" and text:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🌐 Language")
                st.info(lang)
            with col2:
                st.subheader("📝 Transcribed")
                st.write(text)

            with st.spinner("Translating..."):
                eng = translate_to_english(text)
                st.subheader("🌍 English Translation")
                st.success(eng)
        else:
            st.error("Azure couldn't detect speech. Try speaking louder or check your mic settings.")


