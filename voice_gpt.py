import streamlit as st
import whisper
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import tempfile
import io
from pydub import AudioSegment

st.title("🇮🇳 Indian Speech → English (Whisper + NLLB)")

# -----------------------
# Load Whisper tiny
# -----------------------
@st.cache_resource
def load_whisper():
    return whisper.load_model("tiny")

whisper_model = load_whisper()

# -----------------------
# Load NLLB 600M
# -----------------------
@st.cache_resource
def load_nllb():
    model_name = "facebook/nllb-200-distilled-600M"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return tokenizer, model

tokenizer, nllb = load_nllb()

# -----------------------
# Mapping Whisper → NLLB
# -----------------------
LANG_MAP = {
    "hi": "hin_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "kn": "kan_Knda",
    "ml": "mal_Mlym",
    "bn": "ben_Beng",
    "pa": "pan_Guru",
    "gu": "guj_Gujr",
    "mr": "mar_Deva",
    "or": "ory_Orya"
}

# -----------------------
# Convert to WAV 16kHz
# -----------------------
def convert_to_wav(audio_bytes):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio.export(tmp.name, format="wav")
        return tmp.name

# -----------------------
# Translate with NLLB
# -----------------------
def translate_to_english(text, src_code):
    batch = tokenizer(
        text,
        return_tensors="pt",
        src_lang=src_code
    )
    output_tokens = nllb.generate(
        **batch,
        forced_bos_token_id=tokenizer.lang_code_to_id["eng_Latn"]
    )
    return tokenizer.batch_decode(output_tokens, skip_special_tokens=True)[0]

# -----------------------
# UI
# -----------------------
audio = st.audio_input("🎤 Speak in any Indian language...")

if audio:
    if st.button("Transcribe & Translate"):
        st.info("Converting audio...")
        wav_path = convert_to_wav(audio.read())
        st.audio(wav_path)

        st.info("Running Whisper (speech-to-text + language detection)...")
        result = whisper_model.transcribe(wav_path)
        detected = result["language"]
        text = result["text"]

        st.success(f"Detected language: {detected}")
        st.write("### Transcription")
        st.write(text)

        if detected not in LANG_MAP:
            st.error("❌ This language is not mapped for NLLB translation.")
        else:
            src_code = LANG_MAP[detected]
            st.info("Translating using NLLB...")
            english = translate_to_english(text, src_code)

            st.subheader("🇬🇧 English Translation")
            st.success(english)
