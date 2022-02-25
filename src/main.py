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
from views.notes import notes_management

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


from pygments import highlight
from pygments import lexers
from pygments.formatter import Formatter
from pygments.formatters import TerminalTrueColorFormatter


""" ======================= SYNTAX HIGHLIGHT ========================= """

# https://pygments.org/docs/formatterdevelopment/

class CursesFormatter(Formatter):
    def __init__(self, **options):
        Formatter.__init__(self, **options)
        self.styles = {}

        for token, style in self.style:
            col_number = ''
            # a style item is a tuple in the following form:
            # colors are readily specified in hex: 'RRGGBB'
            if style['color']:
                full_col = '%s' % style['color']
                col_number = full_col[-2:] # only last two numbers
            # if style['bold']:
            #     start += 'curses.A_BOLD+'
            # if style['italic']:
            #     start += 'curses.A_ITALIC+'
            # if style['underline']:
            #     start += 'curses.A_UNDERLINE+'
            # else:
                # start += 'curses.A_NORMAL'
            # start = start[:-1] # remove last '+'
            self.styles[token] = col_number # style['color'] returns number of curses.color_pair


    def format(self, tokensource, outfile):
        lastval = ''
        lasttype = None

        tokens = [] # [ (style, text), (style, text), ... ]


        for ttype, value in tokensource:
            while ttype not in self.styles:
                ttype = ttype.parent

            if ttype == lasttype: # if current token type is the same as the last one
                lastval += value
            else:
                if lastval:
                    tokens.append((self.styles[lasttype], lastval))
                    # outfile.write(self.styles[lasttype] + '|' + lastval + '\n')
                lastval = value
                lasttype = ttype

        if lastval:
            tokens.append((self.styles[lasttype], lastval))
            # outfile.write(self.styles[lasttype] + '|' + lastval + '\n')

        # print(tokens)

        """ correction """
        same_style_text = ''
        last_style = None
        if tokens != []:
            style, text = tokens.pop(0)
            if style == '':
                style = "00"
            same_style_text = text
            last_style = style

        while tokens:
            style, text = tokens.pop(0)
            if style == '':
                style = "00"
            if style == last_style: # same style
                same_style_text += text
            else: # new style
                outfile.write(str(last_style)+"|"+str(same_style_text)+'\n')
                last_style = style
                same_style_text = text
    
        if same_style_text:
            outfile.write(str(last_style)+"|"+str(same_style_text)+'\n')


def parse_token(file_name, code):

    try:
        lexer = lexers.get_lexer_for_filename(file_name)
        # curses_format = TerminalTrueColorFormatter(style='curses')
        # curses_format = TerminalTrueColorFormatter()
        curses_format = CursesFormatter(style='curses')
        # print(highlight(code, lexer, curses_format))
        # return

        text = highlight(code, lexer, curses_format)
        raw_tokens = text.splitlines()
        raw_tokens = raw_tokens[:-1] # remove last new line

        # print(tokens)
        # for token in tokens:
            # print(token)

        parsed_tokens = []

        """ parse string tokens to list of tuples (style, text) """
        last_style = ""
        while raw_tokens:
            token = raw_tokens.pop(0)
            parts = token.split("|",1)
            if len(parts) == 2:
                style, text = parts
                last_style = style
                parsed_tokens.append((int(style), text))
            else:
                parsed_tokens.append((int(last_style), '\n'+str(token)))

        """ split tokens to separate lines """
        result = []
        for token in parsed_tokens:
            style, text = token
            text_lines = text.splitlines(True) # keep separator (new line)
            for text_line in text_lines:
                result.append((style, text_line))

        # print(result)
        # for res in result:
            # print(res)

        return result
    except Exception as err:
        # log("get syntax highlight for code | "+str(err))
        return None


"""
-spracovat to tak aby text obsahoval len jeden riadok (nesmie tam byt ziaden \n)
-text musi byt indenticky s lines
-idealne spravit lines ako pole objektov: text, style


-win zmensit o jeden riadok a dva stlpce
-prvy riadok vzdy skipnut a nechat ho na zobrazenie nazvu suboru
-nakreslit okolo win ramcek
"""




""" ======================= START MAIN ========================= """
def main(stdscr):
    log("START")
    stdscr.clear()
    curses.set_escdelay(1)

    """ set coloring """
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()

    init_color_pairs()
    bkgd_color = curses.color_pair(BKGD)
    stdscr.bkgd(' ', bkgd_color)

    """ create screens and windows for TUI """
    screens, windows = create_screens_and_windows(stdscr, curses.LINES, curses.COLS)
    windows.brows.set_cursor(0,0)
    windows.notes.set_cursor(0,0)
    windows.tag.set_cursor(0,0)

    """ load config from file and create framework environment """
    config = load_config_from_file()
    if config is None:
        exit(-1)
    env = Environment(screens, windows, config)

    """ load saved typical notes from file """
    env.typical_notes = load_typical_notes_from_file()


    """ show all main screens """
    stdscr.erase()
    stdscr.refresh()
    refresh_main_screens(stdscr, env)

    """ get current files and dirs """
    env.cwd = get_directory_content()


    y,x = stdscr.getmaxyx()
    half_width = int(x/2)

    # with correction (-2 borders)
    # max_col = half_width-2
    # max_row = 25-2
    # win_y = 0+1
    # win_x = 0+1
    
    max_col = half_width
    # max_col = 70
    max_row = 27
    win_y = 5
    win_x = 5
    screen = curses.newwin(max_row, max_col, win_y, win_x)


    """ rectangle """
    # uly, ulx = win_y-1, win_x-1
    # lry, lrx = win_y+max_row, win_x+max_col

    # stdscr.vline(uly+1, ulx, curses.ACS_VLINE, lry - uly - 1)
    # stdscr.hline(uly, ulx+1, curses.ACS_HLINE, lrx - ulx - 1)
    # stdscr.hline(lry, ulx+1, curses.ACS_HLINE, lrx - ulx - 1)
    # stdscr.vline(uly+1, lrx, curses.ACS_VLINE, lry - uly - 1)

    # stdscr.addch(uly, ulx, curses.ACS_ULCORNER)
    # stdscr.addch(uly, lrx, curses.ACS_URCORNER)
    # stdscr.addch(lry, lrx, curses.ACS_LRCORNER)
    # stdscr.addch(lry, ulx, curses.ACS_LLCORNER)
    # stdscr.refresh()


    screen.erase()
    # screen.border(0)
    screen.move(1,1)

    key = stdscr.getch()

    """ get code from file """
    file_name = '/home/naty/MIT/DP/src/example_c.h'
    # file_name = '/home/naty/MIT/DP/src/example.py'

    with open(file_name,'r') as f:
        lines = f.read().splitlines()
        # code = f.read()


    """ try to get syntax highlight """
    tokens = parse_token(file_name, '\n'.join(lines))
    if tokens is not None:
        for token in tokens:
            style, text = token
            y,x = screen.getyx()
            if y >= max_row-1:
                break
            if x == 0:
                x += 1
            if x+len(text)>max_col-2:
                screen.addstr(y,x,str(text[:max_col-x-1]), curses.color_pair(style))
                if y+1 < max_row-1:
                    screen.move(y+1,1)
            else:
                screen.addstr(y,x,str(text), curses.color_pair(style))
    else:
        # print witout highlight
        pass


    screen.border(0)
    screen.refresh()


    key = stdscr.getch()
    return


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
        elif env.is_notes_mode():
            env = notes_management(stdscr, env)

    """ save typical notes to file """
    save_typical_notes_to_file(env.typical_notes)

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

    c_file = '/home/naty/MIT/DP/src/example_c.h'
    python_file = '/home/naty/MIT/DP/src/example.py'
    with open(python_file,'r') as f:
        code = f.read()

    # tokens = parse_token(python_file, code)
    # exit()

    stdscr = curses.initscr()
    stdscr.keypad(True) # enable read special keys
    curses.wrapper(main)
    curses.endwin()
