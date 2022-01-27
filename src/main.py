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

from config import Config


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

    """ create screen for browsing, editing and showing hint """
    screens, windows = create_screens_and_windows(curses.LINES, curses.COLS)

    """ create config """
    config = create_config(screens, windows)
    config.left_win.set_cursor(0,0)
    config.right_down_win.set_cursor(0,0)
    stdscr.bkgd(' ', bkgd_color)

    """ show all main screens """
    refresh_main_screens(stdscr, config)

    """ get current files and dirs """
    config.cwd = get_directory_content()

    while True:
        print_hint(config)
        if config.is_exit_mode():
            break
        elif config.is_brows_mode():
            config = directory_browsing(stdscr, config)
        elif config.is_view_mode():
            config = file_viewing(stdscr, config)
        elif config.is_tag_mode():
            config = tag_management(stdscr, config)

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
