import pyttsx3

# Initialize the text to speech engine 
engine=pyttsx3.init()  

def speak_text(text):
    engine.say(text)
    engine.runAndWait()

def speak_print(text):
    print("Quadroid:", text)
    speak_text(text)
