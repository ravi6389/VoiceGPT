import streamlit as st
import whisper
import torch
import tempfile
import io
from pydub import AudioSegment
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

st.title("🇮🇳 Speech → English Translator (Whisper + IndicTrans3)")

# -----------------------------
# Load Whisper tiny (FAST)
# -----------------------------
@st.cache_resource
def load_whisper():
    return whisper.load_model("tiny")   # super lightweight for Streamlit Cloud

# -----------------------------
# Load IndicTrans3
# -----------------------------
@st.cache_resource
def load_indictrans3():
    model_name = "ai4bharat/IndicTrans3-beta"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return tokenizer, model

whisper_model = load_whisper()
tokenizer, indic_model = load_indictrans3()

# -----------------------------
# Convert microphone audio → WAV (16k)
# -----------------------------
def convert_to_wav(audio_bytes):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio.export(tmp.name, format="wav")
        return tmp.name

# -----------------------------
# Whisper transcription + language detection
# -----------------------------
def transcribe_with_whisper(wav_path):
    return whisper_model.transcribe(wav_path)

# -----------------------------
# IndicTrans3 translation
# -----------------------------
def translate_indic_to_english(text):
    encoded = tokenizer(text, return_tensors="pt")
    output = indic_model.generate(
        **encoded,
        max_length=350,
        num_beams=4,
        early_stopping=True
    )
    return tokenizer.decode(output[0], skip_special_tokens=True)

# -----------------------------
# UI
# -----------------------------
audio = st.audio_input("🎤 Speak in Hindi, Tamil, Telugu, Kannada, Bengali, Marathi, Gujarati, Malayalam, Punjabi, Odia...")

if audio:
    if st.button("Transcribe & Translate"):
        st.info("Converting audio...")
        wav_path = convert_to_wav(audio.read())

        st.audio(wav_path)

        st.info("Running Whisper (speech-to-text + language detection)...")
        result = transcribe_with_whisper(wav_path)
        detected_lang = result["language"]
        original_text = result["text"]

        st.success(f"Detected Language Code: **{detected_lang}**")
        st.write("### 📝 Transcription")
        st.write(original_text)

        st.info("Translating using IndicTrans3...")
        english = translate_indic_to_english(original_text)

        st.subheader("🇬🇧 English Translation")
        st.success(english)
