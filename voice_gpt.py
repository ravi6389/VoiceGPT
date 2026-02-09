import streamlit as st
import tempfile
import io
import json
import os
from pydub import AudioSegment
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import translate_v3 as translate

st.title("🎤 Indian Speech → English Translation (Google Speech-to-Text + Translate)")

# =========================================
# Load GCP credentials securely via Secrets
# =========================================
def load_gcp_credentials():
    gcp_dict = {k: st.secrets[k] for k in st.secrets}

    gcp_json = json.dumps(gcp_dict)

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


def google_stt_transcribe(wav_path, primary_lang):
    client = get_speech_client()

    with open(wav_path, "rb") as f:
        audio_bytes = f.read()

    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=primary_lang,          # 👈 PRIMARY
        alternative_language_codes=[],        # 👈 We don't want confusion
        enable_automatic_punctuation=True,
        use_enhanced=True,
        model="latest_long"                  # 👈 Best Indian model
    )

    response = client.recognize(config=config, audio=audio)

    if not response.results:
        return ""

    transcript = response.results[0].alternatives[0].transcript
    return transcript


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
# Language Options
# =========================================

LANGUAGES = {
    "Hindi": ("hi-IN", "hi"),
    "Kannada": ("kn-IN", "kn"),
    "Tamil": ("ta-IN", "ta"),
    "Telugu": ("te-IN", "te"),
    "Malayalam": ("ml-IN", "ml")
    # "Bengali": ("bn-IN", "bn"),
    # "Punjabi": ("pa-IN", "pa"),
    # "Gujarati": ("gu-IN", "gu"),
    # "Marathi": ("mr-IN", "mr"),
    # "Odia": ("or-IN", "or"),
}

# User selects language
selected_language = st.selectbox("🌐 Select the language you will speak:", list(LANGUAGES.keys()))
primary_stt_lang, translate_lang_code = LANGUAGES[selected_language]


# =========================================
# User Input
# =========================================
audio = st.audio_input(f"🎤 Speak now in {selected_language}…")

if audio and st.button("Translate"):
    wav = convert_to_wav(audio.read())
    st.audio(wav)

    st.info(f"Transcribing audio using Google Speech-to-Text ({selected_language})…")
    text = google_stt_transcribe(wav, primary_stt_lang)

    if not text:
        st.error("Google could not transcribe your audio. Try again.")
        st.stop()

    st.write("### 🗣 Transcription")
    st.success(text)

    st.info("Translating using Google Cloud Translation API…")
    eng = gcp_translate_text(text, translate_lang_code)

    st.subheader("🇬🇧 English Translation")
    st.success(eng)

