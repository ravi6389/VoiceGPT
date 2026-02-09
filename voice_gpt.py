import streamlit as st
import torch
import gc
import whisper
import tempfile
import io
import json
import os
from pydub import AudioSegment
from google.cloud import translate_v3 as translate

st.title("🇮🇳 Indian Speech → English Translation (GCP + Whisper)")

# =========================================
# Load GCP credentials securely via Secrets
# =========================================
def load_gcp_credentials():
    st.write("DEBUG:", st.secrets)
    st.stop()
    gcp_json = json.dumps(dict(st.secrets))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(gcp_json.encode("utf-8"))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

load_gcp_credentials()

# =========================================
# Google Cloud Translate Client
# =========================================
@st.cache_resource
def get_gcp_client():
    return translate.TranslationServiceClient()

def gcp_translate_text(text, src_lang, project_id="speech-translate-486811"):
    client = get_gcp_client()
    parent = f"projects/{project_id}/locations/global"

    response = client.translate_text(
        contents=[text],
        target_language_code="en",
        source_language_code=src_lang,
        parent=parent
    )
    return response.translations[0].translated_text


# =========================================
# Load Whisper
# =========================================
@st.cache_resource
def load_whisper():
    return whisper.load_model("tiny")


# =========================================
# Audio Conversion
# =========================================
def convert_to_wav(audio_bytes):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio.export(tmp.name, format="wav")
        return tmp.name


# =========================================
# Whisper language → GCP language mapping
# =========================================
LANG_MAP = {
    "hi": "hi",     # Hindi
    "ta": "ta",     # Tamil
    "te": "te",     # Telugu
    "kn": "kn",     # Kannada
    "ml": "ml",     # Malayalam
    "bn": "bn",     # Bengali
    "pa": "pa",     # Punjabi
    "gu": "gu",     # Gujarati
    "mr": "mr",     # Marathi
    "or": "or"      # Odia
}


# =========================================
# User Input
# =========================================
audio = st.audio_input("🎤 Speak something in any Indian language…")

if audio and st.button("Translate"):
    wav = convert_to_wav(audio.read())
    st.audio(wav)

    st.info("Transcribing audio with Whisper…")
    whisper_model = load_whisper()
    result = whisper_model.transcribe(wav)
    text = result["text"]
    lang = result["language"]

    # Free Whisper GPU/CPU memory
    del whisper_model
    gc.collect()
    torch.cuda.empty_cache()

    st.write("### 🗣 Transcription")
    st.success(text)

    if lang not in LANG_MAP:
        st.error(f"Detected language '{lang}' is not supported.")
    else:
        st.info("Translating using Google Cloud Translation API…")
        eng = gcp_translate_text(text, LANG_MAP[lang])

        st.subheader("🇬🇧 English Translation")
        st.success(eng)


