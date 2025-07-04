import datetime
from Main.plays import plays
from Main.speak_text import speak_text

def greet():
    now = datetime.datetime.now()
    hour = now.hour
    plays("response.wav")
    if hour < 12:
        gmtxt = "Good Morning Sir!, How May I Help You?"
        print(gmtxt)
        speak_text(gmtxt)
    elif hour < 18:
        gatxt = "Good Afternoon Sir!, How May I Help You?"
        print(gatxt)
        speak_text(gatxt)
    else:
        getxt = "Good Evening Sir!, How May I Help You?"
        print(getxt)
        speak_text(getxt)