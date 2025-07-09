import json

# Importing From This Main Module
from .quadpath import quadpath

def database(filename):
    file = f'{filename}.json'
    dbpath = quadpath('Databases', file)

    with open(dbpath, "r") as f:
         db = json.load(f)

    return db, dbpath

    
def getdb(filename,key):
    db, dbpath = database(filename)
    dbvalue = db[key]
    return dbvalue


def updatedb(filename,key,value):
    db, dbpath = database(filename)
    db[key] = value

    with open(dbpath, "w") as f:
        json.dump(db, f, indent=4)




        