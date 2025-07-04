import os
import subprocess
import json
from Main.quadpath import quadpath

requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")

configpath=quadpath('Databases', 'config.json')
with open(configpath, "r") as f:
    data = json.load(f)

api_keys = data["api_keys"]
key1 = api_keys["OPENAI_API_KEY"]
key2 = api_keys["NEWS_API_KEY"]

if key1 == "":
    key1 = input("Enter your OPENAI_API_KEY: ")
    api_keys["OPENAI_API_KEY"] = key1
    data["api_keys"] = api_keys

if key2 == "":
    key2 = input("Enter your NEWS_API_KEY: ")
    api_keys["NEWS_API_KEY"] = key2
    data["api_keys"] = api_keys

with open(configpath, "w") as f:
    json.dump(data, f, indent=4)

try:
    # Use subprocess to run the pip command
    result = subprocess.run(["pip", "install", "-r", requirements_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Print the output of the pip command
    print(result.stdout.decode())

    print()
    print("Setup Has Been Completed.. ")
    print("Now Your System is Ready To Use Quadroid")

    config_path = quadpath('Databases', 'config.json')
    with open(config_path, "r") as f:
        config = json.load(f)

    config['setup'] = True

    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

except Exception as e:
    print("An error occurred: {}".format(e))
    print()
    print("Report This Error to https://github.com/MdMobid/Quadroid/issues")
    
print()
w=input("Press Enter Key to Exit: ")
if w=="":
    print()