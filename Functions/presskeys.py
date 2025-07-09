import pyautogui

# Imports From Main Module
from Main.get_audio import get_audio

def presskeys(keys=[]):

    if keys == []:
        keys = get_audio()
        keys = keys.split(" ")
        if "press" in keys:
            if keys[0] == "press":
                keys.remove(keys[0])

    if "control" in keys:
        i = keys.index("control")
        keys[i] = "ctrl"

    kl = len(keys)

    if kl == 3:
        key1, key2, key3 = keys
        pyautogui.hotkey(key1, key2, key3)
    elif kl == 2:
        key1, key2 = keys
        pyautogui.hotkey(key1, key2)
    elif kl == 1:
        key1 = keys
        pyautogui.press(key1)


        