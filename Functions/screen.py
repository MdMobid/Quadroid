import pygetwindow as gw
from Main.db import updatedb, getdb
from Main.plays import plays

def get_screen():
    active_window = gw.getActiveWindow()
    screen_title = active_window.title
    updatedb("config","screen",screen_title)

def output_screen(text):
    screen_title = getdb("config","screen")
    qwindow = gw.getWindowsWithTitle(screen_title)[0]

    # Function to show the output screen
    def show_screen(qwindow):
        plays("blaster.mp3")
        qwindow.maximize()
        qwindow.activate()

    # Function to hide the terminal window
    def hide_screen(qwindow):
        plays("blaster.mp3")
        qwindow.minimize()
        

    # To listen for voice commands
    if "display screen" in text:
        show_screen(qwindow)

    elif "hide screen" in text:
        hide_screen(qwindow)
