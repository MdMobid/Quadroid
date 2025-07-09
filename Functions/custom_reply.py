import json

# Importing Main Module Functions
from Main.quadpath import quadpath
from Main.speak_text import speak_print

rplyfile = quadpath('Databases','customreply.json')
with open(rplyfile, "r") as f:
    replies = json.load(f)

def custom_reply_check(inpt):
    '''Check that the given statement is in custom reply database or not'''
    
    if inpt in replies:
        return True
    else:
        return False

def custom_reply(inpt):
    '''Extract The Custom Reply'''
    
    reply = replies[inpt]
    speak_print(reply)
