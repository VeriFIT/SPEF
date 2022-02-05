
import curses
import curses.ascii


from modules.directory import Directory
from modules.window import Window
from modules.buffer import UserInput

from utils.printing import *
from utils.screens import *
from utils.logger import *


def show_help(stdscr, conf, filter_mode=False):
    curses.curs_set(0)

    screen = conf.center_screen
    win = conf.center_win
    position = 2

    while True:
        """ print something in center screen """
        max_cols = win.end_x - win.begin_x
        max_rows = win.end_y - win.begin_y
        print_help(screen, max_cols, max_rows, conf, filter_mode=filter_mode)

        key = stdscr.getch()
        if key == curses.KEY_F1 or key == ESC:
            rewrite_all_wins(conf)
            return conf
        elif key == curses.KEY_RESIZE:
            conf = resize_all(stdscr, conf)
            screen = conf.center_screen
            win = conf.center_win
        elif curses.ascii.ismeta(key):
            """ CTRL + LEFT / CTRL + RIGHT """
            # https://asecuritysite.com/coding/asc2?val=512%2C768
            if hex(key) == "0x222" or hex(key) == "0x231":
                stdscr_max_y, stdscr_max_x = stdscr.getmaxyx()

                c_win_w = win.end_x - win.begin_x + 1
                c_win_h = win.end_y - win.begin_y + 1
                c_win_y = win.begin_y
                c_win_x = win.begin_x
                if hex(key) == "0x222": # move window to the left side
                    if position == 2:
                        position = 1
                        c_win_x = 0
                    elif position == 3:
                        position = 2
                        c_win_x = int(c_win_w/2)
                elif hex(key) == "0x231": # move window to the right side
                    if position == 1:
                        position = 2
                        c_win_x = int(c_win_w/2)
                    elif position == 2:
                        position = 3
                        c_win_x = c_win_w

                screen = curses.newwin(c_win_h, c_win_w, c_win_y, c_win_x)
                win = Window(c_win_h, c_win_w, c_win_y, c_win_x)
                rewrite_all_wins(conf)

