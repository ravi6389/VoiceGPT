import streamlit as st
import requests
import tempfile
import io
from pydub import AudioSegment

SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]
TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]

LANG_MODELS = {
    "es-ES": "Spanish",
    "fr-FR": "French",
    "it-IT": "Italian"
}

# ---- Convert audio to Azure WAV ----
def convert_to_wav(audio_bytes):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio.export(tmp.name, format="wav")
        return tmp.name

# ---- REST STT for a given language ----
def stt_rest(wav_path, lang):
    url = f"https://{SPEECH_REGION}.stt.speech.microsoft.com/speech/recognition/interactive/cognitiveservices/v1?language={lang}"

    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000"
    }

    with open(wav_path, "rb") as f:
        data = f.read()

    resp = requests.post(url, headers=headers, data=data)
    return resp.json()

# ---- Auto detect among es/fr/it ----
def auto_detect_language(wav_path):
    results = {}

    for code, name in LANG_MODELS.items():
        st.write(f"Testing {name} model...")
        out = stt_rest(wav_path, code)

        status = out.get("RecognitionStatus", "")
        text = out.get("DisplayText", "")

        if status == "Success" and text:
            results[code] = text

    if not results:
        return None, None

    # Choose longest meaningful text
    best_lang = max(results.keys(), key=lambda k: len(results[k]))
    return best_lang, results[best_lang]

# ---- Translate to English ----
def translate_to_english(text):
    url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=en"

    headers = {
        "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, json=[{"text": text}])
    return resp.json()[0]["translations"][0]["text"]

# ---- UI ----
st.title("🌍 Auto-Detect: Spanish / French / Italian → English")

audio = st.audio_input("Speak in Spanish, French, or Italian")

if audio:
    if st.button("Translate"):

        st.info("Converting audio...")
        wav_path = convert_to_wav(audio.read())
        st.audio(wav_path)

        st.info("Detecting language...")
        lang_code, original = auto_detect_language(wav_path)

        if not lang_code:
            st.error("Could not detect language. Try speaking clearly.")
        else:
            st.success(f"Detected: {LANG_MODELS[lang_code]}")
            st.write(f"**Original:** {original}")

            st.info("Translating to English...")
            english = translate_to_english(original)

            st.subheader("🇬🇧 English Translation")
            st.success(english)
