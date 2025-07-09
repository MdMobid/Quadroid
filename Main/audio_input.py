
import speech_recognition as sr

# Importing From This Main Module
from .quadpath import quadpath
from .plays import plays
from .db import getdb
from .speak_text import speak_text, speak_print

def audio_input():  
    '''Function to To Take Audio As Input & Give Output As Text'''

    voice_mode = getdb("config","audio")

    while voice_mode:
        import openai
        
        speak_text("Say Something")
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
        atext=transcript["text"]

        if atext == "" or atext == " ":
            speak_print("I didn't Hear Anything, Please Try Again")
            continue
        if atext != "" or atext != " ":
            print()
            print(f"You said: {atext}")
            break
    
    else:
        print()
        speak_text("Enter Something")
        atext = input("Enter Something: ")
        

    text = atext.lower()
    if text != "":
        if not text[-1].isalnum():
            text = text[:-1]
    #print("tttex",tt-time.time())
    plays("response.wav")

    return atext,text   # [atext] is the real audio/written text and [text] is the modified text