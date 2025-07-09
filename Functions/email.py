import pyautogui
from AppOpener import open as op
from Main.response import generate_response

def email(text):
    #txt = "write an email for me"
    #email_title = input("What's The Title of your Email? ")
    email_title = text
    print("Tell Me Some Specifications Of Your Email")
    #formal = input("Should It be Formal? ")
    formal = "yes"
    #somelse = input("Anything Else You Want To Include? ")
    #if somelse == "no":
    #    somelse = ""
    #else:
    #    somelse = "and " + somelse

    email_txt = f"Write an Email For Me on title {email_title} and Formality:{formal}"

    op("notepad", match_closest=True, output=False)
    email = generate_response(email_txt)
    print("Processing...")
    print(email)

    textn = f"Title: {email_title} \n\n"
    pyautogui.write(textn)
    pyautogui.write(email)

email("Application For Leave")