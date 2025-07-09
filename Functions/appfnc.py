import time
import pyautogui

# Importing Main Module Functions
from Main.speak_text import speak_text
from Main.get_audio import get_audio

# Imports From This Functions Module
from .type import type_while_speaking

def appfnc(app_name):

    if app_name == "google chrome" or app_name == "microsoft edge":
        webfnc()
    if app_name == "notepad":
        notepad()


def webfnc():

    cnt = 0
    time.sleep(2)
    speak_text("What Should I search For You?")

    while True:
        if cnt == 0:
            text1 = get_audio()
            pyautogui.write(str(text1), interval=0.1)
            speak_text("Is That Correct?")
        text2 = get_audio()
        if text2 == "yes":
            pyautogui.press('enter')
            cnt = 0
            break

        elif text2 == "no":
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('delete')
            speak_text("Please Try To Say Again")
            cnt = 0
            continue

        else:
            speak_text("Please Answer In Yes Or No")
            cnt=1
            continue


def notepad():
    
    time.sleep(2)
    speak_text("Do you Want me too type For You?")
    text3 = get_audio()
    if text3 == "yes":
        speak_text("OK Sir, Say Something And I will type for you")
        type_while_speaking()

    elif text3 == "no":
        speak_text("OK Sir")