import streamlit as st
import requests
import uuid
import tempfile
from pydub import AudioSegment

st.set_page_config(page_title="Azure Voice Translator", layout="centered")
st.title("🎙️ Azure REST Speech → English Translator")

# Required Azure Keys
AZ_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZ_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]  # e.g., 'ukwest'

AZ_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
AZ_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]

st.write('AZ_SPEECH_KEY is..', AZ_SPEECH_KEY)
st.write('AZ_SPEECH_REGION is..', AZ_SPEECH_REGION)
def transcribe_and_translate(audio_file):

    # Convert audio to correct WAV format
    audio = AudioSegment.from_file(audio_file)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio.export(tmp.name, format="wav")
        audio_bytes = open(tmp.name, "rb").read()

    # ----------------------------
    # 1️⃣ SPEECH TO TEXT (AUTO-DETECT)
    # ----------------------------

    # stt_url = (
    #     f"https://{AZ_SPEECH_REGION}.stt.speech.microsoft.com/"
    #     "speech/recognition/conversation/cognitiveservices/v1"
    #     "?language=hi-IN"
    # )

    stt_url = (
        f"https://{AZ_SPEECH_REGION}.stt.speech.microsoft.com/"
        "speech/recognition/dictation/cognitiveservices/v1?language=hi-IN"
    )
    
    stt_headers = {
        "Ocp-Apim-Subscription-Key": AZ_SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        "Accept": "application/json",
        "X-Microsoft-OutputFormat": "detailed",
        "X-Microsoft-Detect-Language": "true"
    }

    st.write("🔍 Calling STT endpoint:", stt_url)

    stt_response = requests.post(stt_url, headers=stt_headers, data=audio_bytes)

    if stt_response.status_code != 200:
        return f"STT Error: {stt_response.text}", ""

    stt_json = stt_response.json()
    st.write("STT Response:", stt_json)

    transcript = stt_json.get("DisplayText", "")
    if not transcript:
        return "No speech detected.", ""

    # ----------------------------
    # 2️⃣ TRANSLATE TO ENGLISH
    # ----------------------------

    trans_url = (
        "https://api.cognitive.microsofttranslator.com/translate"
        "?api-version=3.0&to=en"
    )

    trans_headers = {
        "Ocp-Apim-Subscription-Key": AZ_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZ_TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }

    body = [{"text": transcript}]

    trans_response = requests.post(trans_url, headers=trans_headers, json=body)

    if trans_response.status_code != 200:
        return transcript, f"Translation Error: {trans_response.text}"

    translation = trans_response.json()[0]["translations"][0]["text"]

    return transcript, translation


# ----------------------------
# UI Section
# ----------------------------

audio_input = st.audio_input("🎤 Record your voice (Any Indian language)")

if audio_input:
    if st.button("Translate to English"):
        with st.spinner("Processing…"):
            original, translated = transcribe_and_translate(audio_input)

            st.subheader("📝 Original Speech")
            st.write(original)

            st.subheader("🌍 English Translation")
            st.success(translated)








