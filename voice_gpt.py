import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import tempfile

st.title("Azure STT Test")

audio_data = st.audio_input("Record something...")

if audio_data:
    st.success("Audio recorded!")

    # Save recording to temp WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_data.read())
        wav_path = tmp.name

    st.audio(wav_path)

    # Azure STT
    speech_config = speechsdk.SpeechConfig(
        subscription="YOUR_KEY",
        region="centralindia"
    )
    speech_config.speech_recognition_language = "en-IN"

    audio_config = speechsdk.AudioConfig(filename=wav_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)

    result = recognizer.recognize_once()

    st.write("Reason:", result.reason)
    st.write("Text:", result.text)
else:
    st.warning("Please record audio above.")
