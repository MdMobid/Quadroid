import openai
import speech_recognition as sr
from .quadpath import quadpath

def audio_input():  #Function to To Take Audio As Input

    filename = quadpath('Inputs', 'input.wav')
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        source.pause_threshold = 60
        audio = recognizer.listen(source, phrase_time_limit=None, timeout=None)

        with open(filename, "wb") as f:
            f.write(audio.get_wav_data())
            
    audio_file= open(filename, "rb")
    transcript = openai.Audio.translate("whisper-1", audio_file)
    text=transcript["text"]
    return text