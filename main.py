import openai
import speech_recognition as sr
import time

# Imports From The Main Module
from Main.speak_text import speak_text, speak_print
from Main.audio_input import audio_input
from Main.plays import plays
from Main.db import getdb
from Main.logs import addlogs

# Importing Most Important Module Import
from Main.quadroid import quadroid

# Imports From The Functions Module
from Functions.greet import greet
from Functions.screen import get_screen
from Functions.custom_reply import custom_reply, custom_reply_check


# INITIALIZING YOUR OpenAI API KEY HERE FROM DATABASES
openai.api_key = getdb("config","OPENAI_API_KEY")


Flag = 0  # A Flag To Check If Control Is Out Of Assistant
ll = []
go = False  # to check if wake up call is done
c1 = False  # to allow first question after wake up call
sleep = False 
greeted = False 
wklist = getdb("config","wklist")


def main():
    global go
    global c1
    global Flag
    global sleep
    global greeted

    while True:
        if greeted == False:
            greet()
            get_screen()
            greeted=True
            go=True

        if go == False:
         if Flag == 0:
             print()
             plays("response.wav")  # Calling Play Function To Play Sounfile in Sound Effects Folder

         with sr.Microphone() as source:
            recognizer = sr.Recognizer()
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            Flag = 1

        try:
            if go == False:
             transcription = recognizer.recognize_google(audio)
             
             for wakeword in wklist:
                if wakeword in transcription.lower():  
                    plays("wake-up.mp3")
                    go=True
                    c1=True 
                    #time.sleep(2)
                    
            while go: 
                plays("interface.mp3")
                Flag = 0
                atext,text = audio_input()  # Calling audio_input Function, which converts audio to Text

                replycheck = custom_reply_check(text)      # If The User Has Set A Custom Command

                if replycheck:                             # returns true or false after checking
                    custom_reply(text)                     # Extract The Custom Reply

        # If The User Mentions Sleep at the End of The Query, Quadroid Will go To Sleep
                elif "sleep" in text:
                    sleep_word = text.split(" ")[-1]
                    if "sleep" in sleep_word:
                        go=False
                        sleep=True
                        print("Quadroid: Going to Sleep..")
                        speak_text("OK, Going to sleep, Call me When You Need Me")

        # If The User Mentions Some Text it will pass on Quadroid-Function-Handler    
                elif text:
                    quadroid(atext, text)

        except Exception as e:
                if not sleep:
                    speak_text("Didn't Got That, Please Try Again")
                    error_msg = f"ERROR: {e}"
                    print("Quadroid: AN ERROR OCCURRED: {}".format(e))
                    addlogs(error_msg)


if __name__=="__main__":
    setup = getdb("config","setup")
    if setup:
        main()
    else:
        speak_print("You Hadn't Run The Setup File \nRun setup.py and Try Again")