import datetime

def addlogs(log_text):
    now = datetime.datetime.now()
    now = f"[{now}]"

    with open("logs.txt", mode='a') as f:
        f.write(f"{now} : {log_text} \n")

        