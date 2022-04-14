
import curses
import curses.ascii


from modules.directory import Directory
from modules.window import Window
from modules.buffer import UserInput

from utils.printing import *
from utils.screens import *
from utils.logger import *


def show_help(stdscr, env, custom_help=None, exit_key=None):
    curses.curs_set(0)

    screen, win = env.get_center_win(reset=True)
    position = win.position

    if exit_key is None:
        exit_key = [curses.KEY_F1, ESC]

    while True:
        """ print help """
        max_cols = win.end_x - win.begin_x
        max_rows = win.end_y - win.begin_y
        print_help(screen, max_cols, max_rows, env, custom_help=custom_help)

        key = stdscr.getch()

        if key in exit_key or key == curses.KEY_F10:
            rewrite_all_wins(env)
            return env, key
        elif key == curses.KEY_RESIZE:
            env = resize_all(stdscr, env)
            screen, win = env.get_center_win()
            win.reset()
            win.set_position(position, screen)
            rewrite_all_wins(env)
        elif curses.ascii.ismeta(key):
            """ CTRL + LEFT / CTRL + RIGHT """
            # https://asecuritysite.com/coding/asc2?val=512%2C768
            if hex(key) == "0x222" or hex(key) == "0x231":
                if hex(key) == "0x222": # move left
                    if position == 2:
                        position = 1
                    elif position == 3:
                        position = 2
                    win.set_position(position, screen)
                elif hex(key) == "0x231": # move right
                    if position == 1:
                        position = 2
                    elif position == 2:
                        position = 3
                    win.set_position(position, screen)
                rewrite_all_wins(env)
        elif exit_key == []: # if exit key is empty, exit on any key
            rewrite_all_wins(env)
            return env, key

