import time
from AppOpener import open as op
import pyautogui

# Imports From The Main Module
from Main.speak_text import speak_text, speak_print
from Main.response import generate_response
from Main.db import getdb, updatedb
from Main.plays import plays
from Main.audio_input import audio_input

# Imports From The Functions Module
from Functions.openfunc import openfunc
from Functions.newsfunc import newsfunc
from Functions.type import type_while_speaking
from Functions.presskeys import presskeys
from Functions.screen import output_screen

def quadroid(atext, text):
    global c1

    # If The User Mentions news in the Query To Quadroid
    if "tell me some" in text and "news" in text:
        newsfunc(text)  


    # If The User Mentions Open Or Close in The Query.      
    elif "open" in text or "close" in text:
        word1 = text.split(" ")[0]
        if "open" in word1 or "close" in word1:
            openfunc(text)


    # If The User Wants Quadroid should type
    elif text == "type for me":
        speak_text("OK Say SomeThing And I Will Type For You")
        plays("blaster.mp3")
        type_while_speaking()


    # If The User Wants Quadroid should press keyboard keys
    elif "press" in text:
        keys = text.split(" ")
        if keys[0] == "press":
            keys.remove(keys[0])
            presskeys(keys)


    # If The User Wants to Turn ON/OFF The Chat Mode
    elif text == "turn on chat mode" or text == "turn off chat mode":

        if "on" in text:
            mode="ON"
            updatedb("config","audio",False)
        elif "off" in text:
            mode="OFF"
            updatedb("config","audio",True)
            
        speak_text(f"OK Turning {mode} Chat Mode...")
        time.sleep(1)
        plays("blaster.mp3")
        print(f"Quadroid: Chat Mode Has Been Turned {mode}")


    # If The User Wants To See The Output Screen
    elif "display screen" in text or "hide screen" in text:
        output_screen(text)


    # If The User Wants Quadroid To write an email
    elif "write an email for me" in text:
        
        speak_text("Please Give Some More Information:")
        email_title = audio_input()
        op("notepad",match_closest=True,output=False)
        time.sleep(2)
        response = generate_response(str(email_title))
        pyautogui.write(response)
        time.sleep(30)

    # If The User wants to add a custom command
    elif "add a custom reply" in text:
        speak_print("Now Tell me the Line or word which will be replied: ")
        cmd = audio_input()
        speak_print("Now Tell me the reply statement: ")
        reply = audio_input()
        updatedb("customreply",cmd,reply)


    # If Above Conditions Are Not In The Query This Code Will Run (Quadroid Will Handle Now)
    elif text:
        c1=False
        GPT = getdb("config","GPT")
        if GPT:
            # generate the response
            response = generate_response(atext)
            print(f"Quadroid: {response}")
            #print(tt-time.time())

            # read response using GPT-3
            speak_text(response)