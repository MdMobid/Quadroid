import pyautogui

# Imports From The Main Module
from Main.speak_text import speak_text
from Main.plays import plays
from Main.get_audio import get_audio

# Imports From The Functions Module
from Functions.presskeys import presskeys


def type_while_speaking():

    while True:
        plays("interface.mp3")

        try:
            text = get_audio()
            plays("got-it.mp3")

            if text == "stop":
              pyautogui.hotkey('backspace')
              pyautogui.write(".")
              break

            elif text == "stop typing":
                speak_text("OK, I had Stopped Typing")
                break

            elif "press" in text:
                keys = text.split(" ")
                if keys[0] == "press":
                    keys.remove(keys[0])
                    presskeys(keys)

            else: # write the recognized text
                pyautogui.write(text, interval=0.1)
                pyautogui.write(" ")

        except:
            speak_text("Can't Hear You, Please Try Again")
