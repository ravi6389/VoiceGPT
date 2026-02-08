import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import tempfile
import io
import requests
import os
from pydub import AudioSegment, effects, silence

st.set_page_config(page_title="Azure Voice Translator", layout="centered")

# --- Secrets ---
try:
    AZ_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
    AZ_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]
    AZ_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
    AZ_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]
except KeyError as e:
    st.error(f"Missing Secret: {e}. Add it to Streamlit Secrets.")
    st.stop()

# -----------------------
# AUDIO PREPROCESSING
# -----------------------
def prepare_audio_for_azure(audio_bytes):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))

    # Normalize loudness
    audio = effects.normalize(audio)

    # Trim silence
    try:
        audio = silence.strip_silence(audio, silence_len=300, silence_thresh=-45)
    except:
        pass  # if silence strip fails, continue

    # Azure-required format
    audio = audio.set_frame_rate(16000)   # 16 kHz
    audio = audio.set_channels(1)         # mono
    audio = audio.set_sample_width(2)     # 16-bit PCM

    # Ensure minimum length
    if len(audio) < 700:
        audio = audio + audio

    # Save to temp WAV file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio.export(tmp.name, format="wav")
    return tmp.name

# -----------------------
# SPEECH → TEXT (AUTO DETECT)
# -----------------------
def speech_to_text_auto(audio_path):
    speech_config = speechsdk.SpeechConfig(
        subscription=AZ_SPEECH_KEY,
        region=AZ_SPEECH_REGION
    )

    auto_detect = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=["hi-IN", "kn-IN", "ta-IN", "en-IN"]
    )

    audio_config = speechsdk.AudioConfig(filename=audio_path)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
        auto_detect_source_language_config=auto_detect
    )

    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        detected_lang = speechsdk.AutoDetectSourceLanguageResult(result).language
        return result.text, detected_lang

    return None, "unknown"

# -----------------------
# TRANSLATION (TO ENGLISH)
# -----------------------
def translate_to_english(text):
    url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=en"

    headers = {
        "Ocp-Apim-Subscription-Key": AZ_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZ_TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=[{"text": text}])
    return response.json()[0]["translations"][0]["text"]

# -----------------------
# UI
# -----------------------
st.title("🎙️ Indian Language → English Translator")

audio_data = st.audio_input("Record your speech in Hindi, Kannada, Tamil, or English")

if audio_data:
    if st.button("Translate"):
        with st.spinner("Preparing your audio..."):
            temp_wav = prepare_audio_for_azure(audio_data.read())

        with st.spinner("Azure is listening..."):
            text, lang = speech_to_text_auto(temp_wav)

        if text:
            st.success(f"Detected Language: {lang}")
            st.write(f"**Original Speech:** {text}")

            translation = translate_to_english(text)
            st.subheader("English Translation")
            st.success(translation)
        else:
            st.error("Azure could not detect speech. Try speaking louder and avoid silence at the start.")

        # Cleanup
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
