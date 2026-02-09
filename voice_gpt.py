import streamlit as st
import tempfile
import json
import os
import soundfile as sf
import numpy as np
from google.cloud import speech
from google.cloud import translate_v2 as translate


# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------
st.set_page_config(page_title="Indian Speech → English", layout="wide")
st.title("🎤 Indian Speech → English (Google Cloud Only)")


# ---------------------------------------------------------
# Load GCP Credentials from Streamlit Secrets
# ---------------------------------------------------------
def load_gcp_credentials():
    """Writes the [gcp] secrets block into a temp JSON key file."""
    gcp_dict = dict(st.secrets["gcp"])
    json_str = json.dumps(gcp_dict)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(json_str.encode("utf-8"))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name


load_gcp_credentials()


# ---------------------------------------------------------
# Load Google Clients
# ---------------------------------------------------------
@st.cache_resource
def get_gcp_clients():
    speech_client = speech.SpeechClient()
    translate_client = translate.Client()
    return speech_client, translate_client


speech_client, translate_client = get_gcp_clients()


# ---------------------------------------------------------
# Google Cloud Speech-to-Text for Indian Languages
# ---------------------------------------------------------
def transcribe_gcp(audio_array, sample_rate):
    """Convert PCM audio into Indian language transcription using GCP STT."""
    try:
        audio_content = audio_array.tobytes()

        audio = speech.RecognitionAudio(content=audio_content)

        config = speech.RecognitionConfig(
            enable_automatic_punctuation=True,
            language_code="hi-IN",
            alternative_language_codes=[
                "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN",
                "mr-IN", "pa-IN", "gu-IN"
            ],
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            model="latest_long",  # highest accuracy
        )

        response = speech_client.recognize(config=config, audio=audio)

        if not response.results:
            return None

        return response.results[0].alternatives[0].transcript

    except Exception as e:
        st.error(f"Google STT Error: {e}")
        return None


# ---------------------------------------------------------
# Google Cloud Translate → English
# ---------------------------------------------------------
def translate_to_english(text):
    try:
        result = translate_client.translate(text, target_language="en")
        return result["translatedText"]
    except Exception as e:
        st.error(f"Translation Error: {e}")
        return None


# ---------------------------------------------------------
# UI — Audio Recorder
# ---------------------------------------------------------
audio_file = st.file_uploader("🎙 Upload audio file (wav/m4a/mp3)", type=["wav", "mp3", "m4a"])

st.info("Indian languages supported: Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Punjabi, Gujarati, Marathi")

if audio_file and st.button("Transcribe & Translate"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_file.read())
        temp_path = temp_audio.name

    # Load audio into numpy
    audio_data, sample_rate = sf.read(temp_path)

    # If stereo → convert to mono
    if len(audio_data.shape) == 2:
        audio_data = np.mean(audio_data, axis=1)

    st.write("⏳ **Transcribing using Google…**")
    text = transcribe_gcp(audio_data.astype(np.float32), sample_rate)

    if not text:
        st.error("Google Cloud could not transcribe this audio.")
    else:
        st.subheader("🗣 Transcription")
        st.success(text)

        st.write("⏳ **Translating to English…**")
        english = translate_to_english(text)

        st.subheader("🇬🇧 English Translation")
        st.success(english)
