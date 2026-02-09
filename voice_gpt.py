import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import numpy as np
import tempfile
import json
import os
from google.cloud import speech
from google.cloud import translate_v2 as translate


# -------------------------------------------
# PAGE SETTINGS
# -------------------------------------------
st.set_page_config(page_title="🎤 Speak → English", layout="wide")
st.title("🎤 Speak and Translate (Google Cloud Speech-to-Text)")


# -------------------------------------------
# LOAD GCP CREDENTIALS FROM SECRETS
# -------------------------------------------
def load_gcp_credentials():
    gcp_dict = dict(st.secrets)
    json_str = json.dumps(gcp_dict)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(json_str.encode("utf-8"))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name


load_gcp_credentials()


# -------------------------------------------
# LOAD GCP CLIENTS
# -------------------------------------------
@st.cache_resource
def load_gcp_clients():
    return speech.SpeechClient(), translate.Client()


speech_client, translate_client = load_gcp_clients()


# -------------------------------------------
# GOOGLE SPEECH TO TEXT
# -------------------------------------------
def google_transcribe(pcm_audio, sample_rate):
    audio = speech.RecognitionAudio(content=pcm_audio)

    config = speech.RecognitionConfig(
        enable_automatic_punctuation=True,
        language_code="hi-IN",
        alternative_language_codes=[
            "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN",
            "mr-IN", "pa-IN", "gu-IN"
        ],
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        model="latest_long",
    )

    response = speech_client.recognize(config=config, audio=audio)

    if not response.results:
        return None

    return response.results[0].alternatives[0].transcript


# -------------------------------------------
# GOOGLE TRANSLATE
# -------------------------------------------
def translate_to_english(text):
    result = translate_client.translate(text, target_language="en")
    return result["translatedText"]


# -------------------------------------------
# AUDIO PROCESSOR
# -------------------------------------------
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray()
        self.frames.append(pcm)
        return frame


# -------------------------------------------
# WEBRTC MIC UI
# -------------------------------------------
st.subheader("🎙 Speak below")

webrtc_ctx = webrtc_streamer(
    key="speech-demo",
    mode="SENDONLY",
    audio_receiver_size=256,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

if webrtc_ctx and webrtc_ctx.audio_receiver:
    if st.button("⏳ Process Speech"):
        audio_receiver = webrtc_ctx.audio_receiver

        frames = []
        while True:
            try:
                frame = audio_receiver.get_frame(timeout=1)
                frames.append(frame.to_ndarray())
            except:
                break

        if not frames:
            st.warning("No audio captured.")
        else:
            st.success("🎧 Audio captured!")

            pcm = np.concatenate(frames).astype(np.int16).tobytes()
            sample_rate = 48000  # WebRTC default

            st.write("⏳ Transcribing using Google...")
            text = google_transcribe(pcm, sample_rate)

            if text:
                st.subheader("🗣 Transcription")
                st.success(text)

                st.write("⏳ Translating to English...")
                eng = translate_to_english(text)

                st.subheader("🇬🇧 English Translation")
                st.success(eng)
            else:
                st.error("Google could not transcribe your speech.")
