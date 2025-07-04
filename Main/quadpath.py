import os

def quadpath(qfold5="", qfold4="", qfold3="", qfold2="", qfold1="", qfile=""):

    qfold5 = qfold5 or ""  # Set Default Value If qfold5 is None or empty string
    qfold4 = qfold4 or ""
    qfold3 = qfold3 or ""
    qfold2 = qfold2 or ""
    qfold1 = qfold1 or ""
    qfile = qfile or ""

    quad_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), qfold5, qfold4, qfold3, qfold2, qfold1, qfile)
    quad_path = quad_path = quad_path.rstrip("\\") # remove the extra backslash at the end of the file path
    return quad_path