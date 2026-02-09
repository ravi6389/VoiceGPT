import streamlit as st
import tempfile
import io
import json
import os
from pydub import AudioSegment
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import translate_v3 as translate

st.title("🇮🇳 Indian Speech → English Translation (Google Speech-to-Text + Translate)")

# =========================================
# Load GCP credentials securely via Secrets
# =========================================
def load_gcp_credentials():
    # Convert Secrets object → normal dict
    gcp_dict = {k: st.secrets[k] for k in st.secrets}

    # Convert dict → JSON string
    gcp_json = json.dumps(gcp_dict)

    # Write to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(gcp_json.encode("utf-8"))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

load_gcp_credentials()


# =========================================
# Google Cloud Translate Client
# =========================================
@st.cache_resource
def get_gcp_translate_client():
    return translate.TranslationServiceClient()

def gcp_translate_text(text, src_lang, project_id="speech-translate-486811"):
    client = get_gcp_translate_client()
    parent = f"projects/{project_id}/locations/global"

    response = client.translate_text(
        contents=[text],
        target_language_code="en",
        source_language_code=src_lang,
        parent=parent
    )
    return response.translations[0].translated_text


# =========================================
# Google Cloud Speech-to-Text Client
# =========================================
@st.cache_resource
def get_speech_client():
    return speech.SpeechClient()


def google_stt_transcribe(wav_path):
    client = get_speech_client()

    with open(wav_path, "rb") as f:
        audio_bytes = f.read()

    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="hi-IN",
        alternative_language_codes=[
            "hi-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN",
            "bn-IN", "pa-IN", "gu-IN", "mr-IN", "or-IN"
        ],
        enable_automatic_punctuation=True
    )

    response = client.recognize(config=config, audio=audio)

    if not response.results:
        return "", ""

    transcript = response.results[0].alternatives[0].transcript
    detected_lang = response.results[0].language_code if hasattr(response.results[0], "language_code") else ""

    return transcript, detected_lang


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
# Whisper language → GCP language mapping (still used)
# =========================================
LANG_MAP = {
    "hi": "hi",
    "ta": "ta",
    "te": "te",
    "kn": "kn",
    "ml": "ml",
    "bn": "bn",
    "pa": "pa",
    "gu": "gu",
    "mr": "mr",
    "or": "or"
}


# =========================================
# User Input
# =========================================
audio = st.audio_input("🎤 Speak something in any Indian language…")

if audio and st.button("Translate"):
    wav = convert_to_wav(audio.read())
    st.audio(wav)

    st.info("Transcribing audio using Google Speech-to-Text…")
    text, lang_code = google_stt_transcribe(wav)

    if not text:
        st.error("Google could not transcribe your audio. Try again.")
        st.stop()

    st.write("### 🗣 Transcription")
    st.success(text)

    # Google returns lang in format "hi-IN" → convert to "hi"
    lang_short = lang_code.split("-")[0] if lang_code else ""

    if lang_short not in LANG_MAP:
        st.error(f"Detected language '{lang_short}' is not supported.")
    else:
        st.info("Translating using Google Cloud Translation API…")
        eng = gcp_translate_text(text, LANG_MAP[lang_short])

        st.subheader("🇬🇧 English Translation")
        st.success(eng)
