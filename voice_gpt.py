import azure.cognitiveservices.speech as speechsdk

speech_config = speechsdk.SpeechConfig(
    subscription="YOUR_NEW_KEY",
    region="centralindia"
)

speech_config.speech_recognition_language = "en-IN"

audio_config = speechsdk.AudioConfig(filename="sample.wav")
recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)

result = recognizer.recognize_once()

print("Reason:", result.reason)
print("Text:", result.text)
