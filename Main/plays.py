from playsound import playsound

# Importing From This Main Module
from .quadpath import quadpath

# This Function Will get the Path of main.py and will Go to Sound Effets Folder to play 'soundfile'
def plays(soundfile):
    sound_file = quadpath('Sound Effects', soundfile) 
    # Output: sound_file = "\...\Quadroid\Sound Effects\<soundfile>"
    playsound(sound_file)