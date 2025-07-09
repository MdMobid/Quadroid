import subprocess
from Main.quadpath import quadpath
from Main.db import getdb, updatedb
from Main.logs import addlogs

requirements_file = quadpath("requirements.txt")

def addapis():

    key1 = getdb("config","OPENAI_API_KEY")
    key2 = getdb("config","NEWS_API_KEY")

    if key1 == "":
        key1 = input("Enter your OPENAI_API_KEY: ")
        updatedb("config","OPENAI_API_KEY",key1)
        addlogs("OPENAI_API_KEY Was Added")

    if key2 == "":
        key2 = input("Enter your NEWS_API_KEY: ")
        updatedb("config","NEWS_API_KEY",key2)
        addlogs("NEWS_API_KEY Was Added")

try:
    addapis()

    # Use subprocess to run the pip command
    result = subprocess.run(["pip", "install", "-r", requirements_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Print the output of the pip command
    print(result.stdout.decode())

    print()
    print("Setup Has Been Completed.. ")
    print("Now Your System is Ready To Use Quadroid")

    updatedb("config","setup",True)
    addlogs("Quadroid Setup Successful")

except Exception as e:
    error_msg = "An error occurred: {}".format(e)
    print(error_msg)
    addlogs(error_msg)
    print()
    print("Report This Error to https://github.com/MdMobid/Quadroid/issues")
    

# Below Code Is Just To Hold The Screen, So That The User Could See The Outputs
# Else The Output Screen Closes After Running This Code In Some Computers     
print()
w=input("Press Enter Key to Exit: ")
if w=="":
    print()