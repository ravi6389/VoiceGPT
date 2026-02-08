import streamlit as st
import whisper
import torch
import tempfile
import io
from pydub import AudioSegment
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

st.title("🇮🇳 Indian Speech → English Translator (Whisper + IndicTrans2 Lite)")

# -----------------------------
# Load lightweight models
# -----------------------------
@st.cache_resource
def load_whisper():
    return whisper.load_model("tiny")   # FASTEST for Streamlit Cloud

@st.cache_resource
def load_indictrans_lite():
    model_name = "ai4bharat/indictrans2-en-indic-200M"  # Lite model
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)
    return tokenizer, model

whisper_model = load_whisper()
tokenizer, indic_model = load_indictrans_lite()

# -----------------------------
# Convert mic audio → 16k WAV
# -----------------------------
def convert_to_wav(audio_bytes):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio.export(tmp.name, format="wav")
        return tmp.name

# -----------------------------
# Whisper Speech → Text + Language ID
# -----------------------------
def transcribe_and_detect(wav_path):
    return whisper_model.transcribe(wav_path)

# -----------------------------
# IndicTrans2 → English
# -----------------------------
def translate_to_english(text):
    inputs = tokenizer(text, return_tensors="pt")
    output = indic_model.generate(
        **inputs,
        max_length=256,
        num_beams=4,
        early_stopping=True
    )
    return tokenizer.decode(output[0], skip_special_tokens=True)

# -----------------------------
# UI
# -----------------------------
audio = st.audio_input("🎤 Speak in any Indian language (Hindi, Tamil, Telugu, Kannada, Bengali, etc.)")

if audio:
    if st.button("Transcribe & Translate"):
        st.info("Converting audio...")
        wav_path = convert_to_wav(audio.read())
        st.audio(wav_path)

        st.info("Running Whisper (speech-to-text + language detection)...")
        result = transcribe_and_detect(wav_path)

        detected_lang = result["language"]
        original_text = result["text"]

        st.success(f"Detected Language: **{detected_lang}**")
        st.write("### 📝 Transcription")
        st.write(original_text)

        st.info("Translating to English using IndicTrans2 Lite...")
        english = translate_to_english(original_text)

        st.subheader("🇬🇧 English Translation")
        st.success(english)
