import datetime
import os

from pathlib import Path


HOME = str(Path(__file__).parents[2])
LOG_FILE = os.path.join(HOME,"debug.log")
TAG_DIR = os.path.join(HOME,"tags")
REPORT_DIR = os.path.join(HOME,"reports")



def log(message):
    day = datetime.date.today()
    time = datetime.datetime.now().strftime("%X")
    with open(LOG_FILE, 'a') as f:
        f.write("{} {} | {}\n".format(day,time,message))

