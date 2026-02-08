import streamlit as st
import requests
import io
import tempfile
from pydub import AudioSegment

# ----------------------
# Load Secrets
# ----------------------
SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]
TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]

# Languages we will test
LANG_MODELS = {
    "hi-IN": "Hindi",
    "ta-IN": "Tamil",
    "kn-IN": "Kannada",
    "en-IN": "English India"
}

# ----------------------
# Convert audio to Azure-compatible WAV (PCM 16kHz, mono)
# ----------------------
def convert_to_wav(audio_bytes):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio.export(tmp.name, format="wav")
        return tmp.name

# ----------------------
# REST API Speech-to-Text for specific language
# ----------------------
def speech_to_text_rest(wav_path, lang_code):
    url = (f"https://{SPEECH_REGION}.stt.speech.microsoft.com/"
           f"speech/recognition/interactive/cognitiveservices/v1?language={lang_code}")

    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000"
    }

    with open(wav_path, "rb") as f:
        audio_data = f.read()

    response = requests.post(url, headers=headers, data=audio_data)
    return response.json()


    
def detect_script(text):
    for ch in text:
        code = ord(ch)
        if 0x0C80 <= code <= 0x0CFF:
            return "kn-IN"   # Kannada script
        if 0x0B80 <= code <= 0x0BFF:
            return "ta-IN"   # Tamil script
        if 0x0900 <= code <= 0x097F:
            return "hi-IN"   # Hindi/Devanagari script
    return None

# ----------------------
# Choose best result among languages
# ----------------------
def auto_detect_language(wav_path):
    results = {}

    # Step 1 — Run all models
    for code, name in LANG_MODELS.items():
        st.write(f"Testing {name} model...")
        out = speech_to_text_rest(wav_path, code)

        txt = out.get("DisplayText", "")
        status = out.get("RecognitionStatus", "")

        if status != "Success":
            continue
        if not txt:
            continue

        results[code] = txt

    # If nothing worked
    if not results:
        return None, None

    # Step 2 — Script-based override
    for code, txt in results.items():
        detected = detect_script(txt)
        if detected:
            return detected, txt

    # Step 3 — Pick the longest valid text
    best_lang = max(results.keys(), key=lambda k: len(results[k]))
    return best_lang, results[best_lang]

# ----------------------
# Translation to English
# ----------------------
def translate_to_english(text):
    url = ("https://api.cognitive.microsofttranslator.com/"
           "translate?api-version=3.0&to=en")

    headers = {
        "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }

    body = [{"text": text}]
    response = requests.post(url, headers=headers, json=body)
    return response.json()[0]["translations"][0]["text"]

# ----------------------
# UI
# ----------------------
st.title("🎙 Indian Language → English (Auto-Detect via REST API)")

audio_data = st.audio_input("Speak in Hindi, Tamil, Kannada, or English")

if audio_data:
    if st.button("Translate"):

        st.info("Converting audio...")
        wav_path = convert_to_wav(audio_data.read())
        st.audio(wav_path)

        st.info("Detecting language... (trying 4 models)")
        lang_code, original_text = auto_detect_language(wav_path)

        if not lang_code:
            st.error("Could not detect any language. Try speaking more clearly.")
        else:
            st.success(f"Detected Language: {LANG_MODELS[lang_code]}")
            st.write(f"**Original:** {original_text}")

            st.info("Translating to English...")
            english = translate_to_english(original_text)

            st.subheader("🇬🇧 English Translation")
            st.success(english)




