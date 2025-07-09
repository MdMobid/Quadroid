import os

def quadpath(qfolder3="", qfolder2="", qfolder1="", qfile=""):

    qfolder3 = qfolder3 or ""  # Set Default Value If qfold3 is None or empty string
    qfolder2 = qfolder2 or ""
    qfolder1 = qfolder1 or ""
    qfile = qfile or ""

    quad_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), qfolder3, qfolder2, qfolder1, qfile)
    quad_path = quad_path = quad_path.rstrip("\\") # remove the extra backslash at the end of the file path
    return quad_path