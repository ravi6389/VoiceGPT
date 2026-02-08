import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import tempfile
import io
import requests
import os
from pydub import AudioSegment, effects, silence

st.set_page_config(page_title="Azure Voice Translator", layout="centered")

# -----------------------
# Load Secrets
# -----------------------
try:
    AZ_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
    AZ_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]
    AZ_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
    AZ_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]
except KeyError as e:
    st.error(f"Missing secret: {e}. Please add it to Streamlit secrets.")
    st.stop()

# -----------------------
# DEBUG: Inspect Audio
# -----------------------
def debug_audio(audio_bytes):
    st.subheader("🔎 RAW AUDIO DEBUG INFO")

    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    except Exception as e:
        st.error(f"Audio could not be decoded: {e}")
        return None

    st.write({
        "duration_ms": len(audio),
        "channels": audio.channels,
        "sample_width_bytes": audio.sample_width,
        "frame_rate_hz": audio.frame_rate,
        "loudness_dBFS": audio.dBFS,
        "max_dBFS": audio.max_dBFS
    })

    # Save raw audio and play it in UI
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as raw_tmp:
        audio.export(raw_tmp.name, format="wav")
        st.audio(raw_tmp.name)
        st.info("👆 RAW INPUT AUDIO (before conversion)")

    return audio

# -----------------------
# Preprocess audio for Azure STT
# -----------------------
def prepare_audio_for_azure(audio_bytes):

    audio = debug_audio(audio_bytes)

    if audio is None:
        st.error("Audio cannot be processed.")
        return None

    st.subheader("🎚 Audio Processing")

    # Normalize volume
    audio = effects.normalize(audio)

    # Remove silence
    try:
        audio = silence.strip_silence(audio, silence_len=300, silence_thresh=-45)
    except:
        pass

    # Convert to Azure required format
    audio = audio.set_frame_rate(16000)    # 16kHz
    audio = audio.set_channels(1)          # mono
    audio = audio.set_sample_width(2)      # 16-bit PCM

    # Ensure minimum duration
    if len(audio) < 700:
        audio = audio + audio

    # Debug the converted audio
    st.write({
        "converted_duration_ms": len(audio),
        "converted_loudness_dBFS": audio.dBFS,
        "channels": audio.channels,
        "frame_rate": audio.frame_rate,
        "sample_width": audio.sample_width
    })

    # Export final WAV
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio.export(tmp.name, format="wav")
        st.audio(tmp.name)
        st.success("👆 FINAL WAV SENT TO AZURE")

        return tmp.name


# -----------------------
# Speech → Text (Auto detection)
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

    return None, None


# -----------------------
# Translate to English
# -----------------------
def translate_to_english(text):
    endpoint = f"https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=en"

    headers = {
        "Ocp-Apim-Subscription-Key": AZ_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZ_TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }

    resp = requests.post(endpoint, headers=headers, json=[{"text": text}])
    return resp.json()[0]["translations"][0]["text"]


# -----------------------
# UI
# -----------------------
st.title("🎙 Indian Languages → English Translator")
audio_data = st.audio_input("Record your voice in Hindi, Tamil, Kannada, or English")

if audio_data:
    if st.button("Translate"):
        with st.spinner("Processing your recording..."):
            temp_wav = prepare_audio_for_azure(audio_data.read())

        if temp_wav is None:
            st.error("Audio preprocessing failed.")
            st.stop()

        with st.spinner("Azure is listening..."):
            text, lang = speech_to_text_auto(temp_wav)

        # Cleanup temp
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

        # Display results
        if text:
            st.success(f"Detected Language: {lang}")
            st.write(f"**Transcribed Text:** {text}")

            translation = translate_to_english(text)
            st.subheader("English Translation")
            st.success(translation)
        else:
            st.error("❌ Azure could NOT detect speech. See debug info above.")
            st.warning("Try speaking louder, avoid silence, and ensure your mic is active.")
