import openai
import speech_recognition as sr
import time
import json

# Imports From The Main Module
from Main.speak_text import speak_text
from Main.audio_input import audio_input
from Main.response import generate_response
from Main.quadpath import quadpath
from Main.plays import plays

# Imports From The Functions Module
from Functions.openfunc import openfunc
from Functions.newsfunc import newsfunc
from Functions.greet import greet


# Imports From The Databases
congif_path = quadpath('Databases', 'config.json')
with open(congif_path, "r") as f:
    data = json.load(f)

# INITIALIZING YOUR OpenAI API KEY HERE FROM DATABASES
api_keys = data["api_keys"]
openai.api_key = api_keys["OPENAI_API_KEY"]


x=0  # A Flag To Check If Control Is Out Of Assistant
ll=[]
go=False  # to check if wake up call is done
c1=False  # to allow first question after wake up call
sleep=False
greeted=False


def main():
    global go
    global c1
    global x
    global sleep
    global greeted
    
    while True:
        if greeted == False:
            greet()
            greeted=True
            go=True

        tt=time.time()
        if go == False:
         if x == 0:
             print()
             plays("response.wav")  # Calling Play Function To Play Sounfile in Sound Effects Folder

         with sr.Microphone() as source:
            recognizer = sr.Recognizer()
            audio = recognizer.listen(source)
            x=1

        try:
            if go == False:
             transcription = recognizer.recognize_google(audio)
        
             if "hey" in transcription.lower() :  
                plays("wake-up.mp3")
                go=True
                c1=True 
                #time.sleep(2)
                
            while go: 
                plays("interface.mp3")
                speak_text("Say Something")
                tt1=time.time()
                c2=int(time.time()-tt1)
                
                x=0
                atext = audio_input()  # Calling audio_input Function, which converts audio to Text
                text = atext.lower()
                if text != "":
                    if not text[-1].isalnum():
                        text = text[:-1]
                #print("tttex",tt-time.time())
                print()
                print(f"You said: {atext}")
                plays("response.wav")

                # If The User Says Thank You To Quadroid
                if text == "thank you" :
                    print("Quadroid: Mention Not Sir! What Can i do for you next?" )
                    speak_text("Mention Not Sir! What Can i do for you next?")
                    

                # If The User Mentions news in the Query To Quadroid
                elif "tell me some" in text and "news" in text:
                    topic_word = text.split(" ")[3]
                    newsfunc(topic_word)


                # If The User Mentions Sleep at the End of The Query, Quadroid Will go To Sleep
                elif "sleep" in text:
                    sleep_word = text.split(" ")[-1]
                    if "sleep" in sleep_word:
                        go=False
                        sleep=True
                        print("Quadroid: Going to Sleep..")
                        speak_text("OK, Going to sleep, Call me When You Need Me")   


                # If The User Mentions Open Or Close in The Query.      
                elif "open" in text or "close" in text:
                    word1 = text.split(" ")[0]
                    if "open" in word1 or "close" in word1:
                        openfunc(text)


                # If Above Conditions Are Not In The Query This Code Will Run (Quadroid Will Handle Now)
                elif text:
                    c1=False
                    tt=time.time()

                    # generate the response
                    response = generate_response(atext)
                    print(f"Quadroid: {response}")
                    print(tt-time.time())

                    # read response using GPT-3
                    speak_text(response)

                # If The User Says Nothing    
                else:
                    print("You Said Nothing, Please Try Again")
                    speak_text("Please Try Again")

        except Exception as e:
                if not sleep:
                    speak_text("Didn't Got That, Please Try Again")
                    print("An error occurred: {}".format(e))

if __name__=="__main__":
    setup = data["setup"]
    if setup:
        main()
    else:
        print("You Hadn't Run The Setup File")
        print("Run setup.py and Try Again")