#!/usr/bin/env python3

import curses
import curses.ascii
import datetime
import json
import yaml
import os
import re
import sys
import fnmatch
import glob


from views.browsing import get_directory_content, directory_browsing
from views.filtering import filter_management
from views.viewing import file_viewing
from views.tags import tag_management
from views.help import show_help

from modules.buffer import Buffer, Report, UserInput
from modules.directory import Directory
from modules.window import Window, Cursor

from utils.loading import *
from utils.screens import *
from utils.coloring import *
from utils.printing import *
from utils.logger import *

from config import Environment


""" hladanie cesty projektu v ktorom su odovzdane riesenia
    TODO: 1
    -v aktualnej ceste buffer.file_name sa bude hladat cesta suboru s projektom
    -hlada sa od definovaneho HOME az kym nenajde xlogin00 subor
    -xlogin00 sa najde podla regexu x[a-z][a-z][a-z][a-z][a-z][0-9][0-9]
    -teda z cesty HOME/.../.../xlogin00/dir/file bude subor projektu .../...

    TODO: 2
    -kazdy projekt bude nejak reprezentovany
    -nazvy/cesty projektovych suborov budu niekde ulozene
    -prehlada sa zoznam projektov
    -skontroluje sa ci aktualna cesta buffer.file_name ma prefix zhodny s niektorym projektom
"""



""" ======================= START MAIN ========================= """
def main(stdscr):
    log("START")
    stdscr.clear()
    curses.set_escdelay(1)

    """ set coloring """
    curses.start_color()
    curses.use_default_colors()

    init_color_pairs()
    bkgd_color = curses.color_pair(BKGD)
    stdscr.bkgd(' ', bkgd_color)

    """ create screens and windows for TUI """
    screens, windows = create_screens_and_windows(curses.LINES, curses.COLS)
    windows.left.set_cursor(0,0)
    windows.right_down.set_cursor(0,0)

    """ load config from file and create framework environment """
    dir_path = os.path.dirname(__file__)
    conf_file = os.path.join(dir_path, "config.yaml")
    try:
        with open(conf_file, 'r') as f:
            config = yaml.safe_load(f)
        env = Environment(screens, windows, config)
    except Exception as err:
        log("cannot load config file | "+str(err))
        exit(-1)

    """ show all main screens """
    stdscr.erase()
    stdscr.refresh()
    refresh_main_screens(env)

    """ get current files and dirs """
    env.cwd = get_directory_content()

    while True:

        print_hint(env)
        if env.is_exit_mode():
            break
        elif env.is_brows_mode():
            env = directory_browsing(stdscr, env)
        elif env.is_view_mode():
            env = file_viewing(stdscr, env)
        elif env.is_tag_mode():
            env = tag_management(stdscr, env)

    log("END")
""" ======================= END MAIN ========================= """



# TODO: cache all tags and reports to local files TAG_DIR and REPORT_DIR

def preparation():
    """ clear log file """
    with open(LOG_FILE, 'w+'): pass

    """ create dirs for tags and reports """
    if not os.path.exists(TAG_DIR):
        os.makedirs(TAG_DIR)
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)


if __name__ == "__main__":
    preparation()

    stdscr = curses.initscr()
    stdscr.keypad(True) # enable read special keys
    curses.wrapper(main)
    curses.endwin()
