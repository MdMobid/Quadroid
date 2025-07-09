import speech_recognition as sr

def get_audio():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        txt = recognizer.recognize_google(audio)
        txt = txt.lower()
    except sr.UnknownValueError:
        pass

    return txt