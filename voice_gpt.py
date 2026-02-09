import streamlit as st
from audiorecorder import audiorecorder
import numpy as np
import soundfile as sf
import tempfile
import json
import os
from google.cloud import speech
from google.cloud import translate_v2 as translate


# -------------------------------------------
# PAGE SETTINGS
# -------------------------------------------
st.set_page_config(page_title="🎤 Speak → English", layout="centered")
st.title("🎤 Speak and Translate (Google STT)")


# -------------------------------------------
# LOAD GCP CREDENTIALS FROM SECRETS
# -------------------------------------------
def load_gcp_credentials():
    gcp_dict = dict(st.secrets)   # you asked to use direct secrets
    json_str = json.dumps(gcp_dict)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(json_str.encode("utf-8"))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name


load_gcp_credentials()


# -------------------------------------------
# LOAD GCP CLIENTS
# -------------------------------------------
@st.cache_resource
def load_gcp_clients():
    return speech.SpeechClient(), translate.Client()


speech_client, translate_client = load_gcp_clients()


# -------------------------------------------
# GOOGLE SPEECH TO TEXT
# -------------------------------------------
def google_transcribe(pcm_audio, sample_rate):
    audio = speech.RecognitionAudio(content=pcm_audio)

    config = speech.RecognitionConfig(
        enable_automatic_punctuation=True,
        language_code="hi-IN",
        alternative_language_codes=[
            "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN",
            "mr-IN", "pa-IN", "gu-IN"
        ],
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        model="latest_long",
    )

    response = speech_client.recognize(config=config, audio=audio)

    if not response.results:
        return None

    return response.results[0].alternatives[0].transcript


# -------------------------------------------
# GOOGLE TRANSLATE
# -------------------------------------------
def translate_to_english(text):
    result = translate_client.translate(text, target_language="en")
    return result["translatedText"]


# -------------------------------------------
# AUDIO RECORDER UI
# -------------------------------------------
st.subheader("🎙 Speak Below")

audio = audiorecorder("Start Recording", "Stop Recording")

if len(audio) > 0:
    st.success("🎧 Recording complete!")
    st.audio(audio.tobytes(), format="audio/wav")

    # Save to WAV
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        wav_path = temp_audio.name
        sf.write(wav_path, np.array(audio), 44100)  # recorder always records at 44.1kHz

    # Read PCM bytes
    pcm_data, sr = sf.read(wav_path, dtype="int16")
    pcm_bytes = pcm_data.tobytes()

    if st.button("⏳ Transcribe & Translate"):
        st.write("⏳ Transcribing using Google...")

        text = google_transcribe(pcm_bytes, sr)

        if text:
            st.subheader("🗣 Transcription")
            st.success(text)

            st.write("⏳ Translating to English...")
            eng = translate_to_english(text)

            st.subheader("🇬🇧 English Translation")
            st.success(eng)
        else:
            st.error("Google could not transcribe your speech.")
