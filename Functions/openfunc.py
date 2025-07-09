import os
import json

# Importing External Required Functions
import difflib
import AppOpener
from webbrowser import open as opweb
from AppOpener import open as op, close

# Importing Main Module Functions
from Main.speak_text import speak_text, speak_print
from Functions.appfnc import appfnc


def apps():
  module_path = os.path.abspath(os.path.dirname(AppOpener.__file__))
  data_file_path = os.path.join(module_path, "Data", "data.json")

  with open(data_file_path, "r") as f:
      data = json.load(f)
      app_names = list(data.keys())

  return app_names


def openfunc(query):

  fncapps = ["google chrome", "microsoft edge", "notepad"]

  if "in web" in query:
    x = query.replace("open ", "").replace(" in web", "").strip()
    if "." not in x:
      x=x+" "
    
    speak_print(f"OPENING {x} IN WEB")
    opweb(x)


  elif "close " in query:
    app_name = query.replace("close ","").strip()
    speak_text(f"CLOSING {app_name}")
    close(app_name, match_closest=True, output=True)


  elif "open " in query:
    app_name = query.replace("open ","")
    app_names = apps()

    closest_matches = difflib.get_close_matches(app_name, app_names, n=1, cutoff=0.6)
    if closest_matches:
      closest_match = closest_matches[0]
      app_index = app_names.index(closest_match)
      app_name = app_names[app_index]
      
      speak_print(f"OPENING {app_name}")
      op(app_name, match_closest=True, output=False)
      
      if app_name in fncapps:
        appfnc(app_name)

    else:
      speak_print(f"ERROR: {app_name} Is Not Available In Your System")
