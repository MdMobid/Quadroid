from webbrowser import open as ope
from AppOpener import open as op, close
import AppOpener
import os
from Main.speak_text import speak_text
import json
import difflib


module_path = os.path.abspath(os.path.dirname(AppOpener.__file__))
data_file_path = os.path.join(module_path, "Data", "data.json")

with open(data_file_path, "r") as f:
    data = json.load(f)
    app_names = list(data.keys())

    

def openfunc(query):
  query = query.lower()

  if "in web" in query:
    x = query.replace("open ", "").replace(" in web", "").strip()

    if x[-1] == ".":
      x = x[:-1]
    
    if "." not in x:
      if x[-1] != ".":
        x=x+" "
    
    text1 = f"OPENING {x} IN WEB"
    print(text1)
    speak_text(text1)
    ope(x)

  elif "close " in query:
    app_name = query.replace("close ","").strip()
    text2 = f"CLOSING {app_name}"
    #print(text2)
    speak_text(text2)
    close(app_name, match_closest=True, output=True)


  elif "open " in query:
    app_name = query.replace("open ","")
    text2 = f"OPENING {app_name}"

    closest_matches = difflib.get_close_matches(app_name, app_names, n=1, cutoff=0.6)
    if closest_matches:
      print(text2)
      speak_text(text2)
      op(app_name, match_closest=True, output=False)
    else:
      print(f"ERROR: {app_name} Is Not Available In Your System")
      speak_text(f"{app_name} Is Not Available In Your System")




      
