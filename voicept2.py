import streamlit as st

st.set_page_config(page_title="Audio Recorder & Replay", page_icon="🎙️")

st.title("🎙️ Cloud Microphone App")

# Initialize session state to store audio
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# 1. Recording Widget
audio_data = st.audio_input("Record your message")

# If a new recording is made, save it to session state
if audio_data:
    st.session_state.last_audio = audio_data.read()

# 2. Replay Section
if st.session_state.last_audio:
    st.write("---")
    st.subheader("Controls")
    
    # Standard player (shows up automatically)
    st.write("Current Recording:")
    st.audio(st.session_state.last_audio)
    
    # Custom Replay Button (triggers the audio again)
    if st.button("🔄 Replay Sound"):
        # This re-renders the audio component specifically for playback
        st.audio(st.session_state.last_audio, autoplay=True)
        st.toast("Replaying...")

    # Optional: Download Button
    st.download_button(
        label="📥 Download Recording",
        data=st.session_state.last_audio,
        file_name="cloud_recording.wav",
        mime="audio/wav"
    )
else:
    st.info("Record something above to enable the replay button.")
