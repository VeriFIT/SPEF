
import curses
import curses.ascii


from modules.directory import Directory
from modules.window import Window
from modules.buffer import UserInput

# TODO: premiestnit !!!
from views.help import rewrite_all_wins

from utils.printing import *
from utils.screens import *
from utils.logger import *


ESC = 27


def get_user_input(stdscr, conf, title=None):
    curses.curs_set(1)

    screen = conf.center_screen
    win = conf.center_win
    position = win.position

    user_input = UserInput()

    while True:
        """ show user input """
        max_cols = win.end_x - win.begin_x
        max_rows = win.end_y - win.begin_y
        color = curses.color_pair(TAG_MGMT)

        row, col = show_user_input(screen, user_input, max_rows, max_cols, conf, color=color, title=title)
        stdscr.move(win.begin_y + row, win.begin_x + col)


        key = stdscr.getch()
        if key == curses.KEY_F1 or key == ESC:
            rewrite_all_wins(stdscr, conf)
            return conf, None
        elif key == curses.KEY_RESIZE:
            conf = resize_all(stdscr, conf)
            screen = conf.center_screen
            win = conf.center_win
        # ======================= INPUT =======================
        elif key == curses.KEY_DC:
            user_input.delete_symbol(win)
        elif key == curses.KEY_BACKSPACE:
            if user_input.pointer > 0:
                user_input.left(win)
                user_input.delete_symbol(win)
        elif key == curses.ascii.NL:
            rewrite_all_wins(stdscr, conf)
            return conf, user_input.text
        elif curses.ascii.isprint(key):
            user_input.insert_symbol(win, chr(key))
        elif curses.ascii.ismeta(key):
            """ CTRL + LEFT / CTRL + RIGHT """
            # https://asecuritysite.com/coding/asc2?val=512%2C768
            if hex(key) == "0x222" or hex(key) == "0x231":
                stdscr_max_y, stdscr_max_x = stdscr.getmaxyx()

                c_win_w = win.end_x - win.begin_x + 1
                c_win_h = win.end_y - win.begin_y + 1
                c_win_y = win.begin_y
                c_win_x = win.begin_x
                if hex(key) == "0x222": # move left
                    if position == 2:
                        position = 1
                        c_win_x = 0
                    elif position == 3:
                        position = 2
                        c_win_x = int(c_win_w/2)
                elif hex(key) == "0x231": # move right
                    if position == 1:
                        position = 2
                        c_win_x = int(c_win_w/2)
                    elif position == 2:
                        position = 3
                        c_win_x = c_win_w

                screen = curses.newwin(c_win_h, c_win_w, c_win_y, c_win_x)
                win = Window(c_win_h, c_win_w, c_win_y, c_win_x)
                win.set_position = position
                conf.center_screen = screen
                conf.center_win = win
                rewrite_all_wins(stdscr, conf)



