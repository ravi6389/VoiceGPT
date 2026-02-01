import streamlit as st
import streamlit.components.v1 as components
import tempfile
import requests
import azure.cognitiveservices.speech as speechsdk

st.set_page_config(page_title="Voice Translator", layout="centered")

st.title("🎙️ Voice → English Translator (Streamlit Cloud Compatible)")

# ------------------ AZURE KEYS ------------------
AZURE_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_SPEECH_REGION = st.secrets["AZURE_SPEECH_REGION"]

AZURE_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
AZURE_TRANSLATOR_REGION = st.secrets["AZURE_TRANSLATOR_REGION"]

TRANSLATOR_ENDPOINT = (
    "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"
)

# ----------------- RECORDING COMPONENT -----------------
st.subheader("🎤 Step 1: Record your voice")

js_code = """
<div>
<button id="startBtn">🎙️ Start Recording</button>
<button id="stopBtn">⛔ Stop Recording</button>
<p id="status"></p>
</div>

<script>
let mediaRecorder;
let audioChunks = [];

document.getElementById("startBtn").onclick = async function() {
    document.getElementById("status").innerHTML = "Recording...";
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();

    audioChunks = [];
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
};

document.getElementById("stopBtn").onclick = function() {
    document.getElementById("status").innerHTML = "Processing...";
    mediaRecorder.stop();

    mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunks, { type: "audio/webm" });
        const file = new File([blob], "recording.webm");

        // Put the file inside Streamlit's uploader
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        document.querySelector('input[type=file]').files = dataTransfer.files;

        document.getElementById("status").innerHTML = "Recording saved!";
    };
};
</script>
"""

components.html(js_code, height=200)

uploaded_audio = st.file_uploader("Your recorded audio:", type=["webm", "wav"])

# ------------ SPEECH TO TEXT ----------------
def transcribe_audio(path):
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION
    )

    auto_lang = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=[
            "hi-IN","ta-IN","te-IN","ml-IN","kn-IN","mr-IN",
            "bn-IN","gu-IN","pa-IN","ur-IN","en-US"
        ]
    )

    audio_config = speechsdk.AudioConfig(filename=path)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
        auto_detect_source_language_config=auto_lang
    )

    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text

    return "⚠ Could not transcribe."

# ------------ TRANSLATE ----------------
def translate_to_english(text):
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json",
    }

    body = [{"text": text}]

    response = requests.post(
        TRANSLATOR_ENDPOINT + "&to=en",
        headers=headers,
        json=body
    )

    data = response.json()
    st.wtite(data)
    return data[0]["translations"][0]["text"]


# ------------ MAIN ACTION ----------------
if uploaded_audio:
    st.audio(uploaded_audio)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    temp.write(uploaded_audio.read())
    temp.flush()

    if st.button("📝 Transcribe & Translate"):
        st.info("Transcribing…")

        text = transcribe_audio(temp.name)
        st.subheader("📝 Transcription")
        st.write(text)

        st.info("Translating to English…")
        english = translate_to_english(text)

        st.subheader("🌍 English Translation")
        st.success(english)

