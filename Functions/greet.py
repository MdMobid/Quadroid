import datetime

# Importing Main Module Functions
from Main.plays import plays
from Main.speak_text import speak_print

def greet():
    now = datetime.datetime.now()
    hour = now.hour
    plays("response.wav")
    if hour < 12:
        speak_print("Good Morning Sir!, How May I Help You?")
    elif hour < 18:
        speak_print("Good Afternoon Sir!, How May I Help You?")
    else:
        speak_print("Good Evening Sir!, How May I Help You?")