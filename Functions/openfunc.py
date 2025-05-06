from webbrowser import open as ope
from AppOpener import open as op, close
from Functions.speak_text import speak_text

def openfunc(query):

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
    print(text2)
    speak_text(text2)
    close(app_name, match_closest=True, output=False) # App will be close be it matches little bit too (Without printing context (like CLOSING <app_name>))

  elif "open " in query:
    app_name = query.replace("open ","")
    text2 = f"OPENING {app_name}"
    speak_text(text2)
    op(app_name, match_closest=True) # App will be open be it matches little bit too