import streamlit as st
import torch
import gc
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import whisper
import tempfile
import io
from pydub import AudioSegment

st.title("🇮🇳 Indian Speech → English (Optimized for Streamlit Cloud)")

# ----------------------------
# Load Whisper lazily
# ----------------------------
@st.cache_resource
def load_whisper():
    return whisper.load_model("tiny")

# ----------------------------
# Load NLLB lazily
# ----------------------------
@st.cache_resource
def load_nllb():
    model_name = "facebook/nllb-200-distilled-600M"
    tok = AutoTokenizer.from_pretrained(model_name)
    mdl = AutoModelForSeq2SeqLM.from_pretrained(model_name, torch_dtype=torch.float16)
    return tok, mdl

# Convert to wav 16k
def convert_to_wav(audio_bytes):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio.export(tmp.name, format="wav")
        return tmp.name

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

audio = st.audio_input("🎤 Speak...")

if audio and st.button("Translate"):
    wav = convert_to_wav(audio.read())
    st.audio(wav)

    st.info("Transcribing with Whisper…")
    whisper_model = load_whisper()
    result = whisper_model.transcribe(wav)
    text = result["text"]
    lang = result["language"]

    # Free Whisper from memory
    del whisper_model
    gc.collect()
    torch.cuda.empty_cache()

    st.write("### 🗣 Transcription")
    st.write(text)

    if lang not in LANG_MAP:
        st.error("Language not supported by NLLB.")
    else:
        st.info("Translating with NLLB…")
        tokenizer, nllb = load_nllb()

        encoded = tokenizer(text, return_tensors="pt", src_lang=LANG_MAP[lang])
        output_tokens = nllb.generate(
            **encoded,
            forced_bos_token_id=tokenizer.lang_code_to_id["eng_Latn"]
        )
        eng = tokenizer.decode(output_tokens[0], skip_special_tokens=True)

        st.subheader("🇬🇧 English Translation")
        st.success(eng)
