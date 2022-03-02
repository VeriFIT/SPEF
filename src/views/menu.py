
import curses
import curses.ascii
import traceback

from modules.directory import Directory
from modules.window import Window
from modules.buffer import UserInput


from utils.printing import *
from utils.screens import *
from utils.logger import *


ESC = 27

"""
menu_options = []
returns env, option
"""
def brows_menu(stdscr, env, menu_options, color=None, title=None):
    curses.curs_set(0)

    screen, win = env.get_center_win(reset=True, row=0, col=0)
    position = win.position
    win.set_border(0)

    rewrite_all_wins(env)


    while True:
        """ show menu options """
        max_cols = win.end_x - win.begin_x - 1
        max_rows = win.end_y - win.begin_y - 1

        show_menu(screen, win, menu_options, max_rows, max_cols, env, color=color, title=title)


        key = stdscr.getch()

        try:
            # ======================= EXIT =======================
            if key == curses.KEY_F1 or key == ESC:
                rewrite_all_wins(env)
                return env, None
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                env = resize_all(stdscr, env)
                screen, win = env.get_center_win()
                win.reset()
                win.set_position(position, screen)
                rewrite_all_wins(env)
            # ======================= INPUT =======================
            elif key == curses.KEY_UP:
                win.up(menu_options, use_restrictions=False)
            elif key == curses.KEY_DOWN:
                win.down(menu_options, use_restrictions=False)
            elif key == curses.ascii.NL: # execute selected option
                return env, win.cursor.row
            elif curses.ascii.ismeta(key):
                """ CTRL + LEFT / CTRL + RIGHT """
                # https://asecuritysite.com/coding/asc2?val=512%2C768
                if hex(key) == "0x222" or hex(key) == "0x231":
                    if hex(key) == "0x222": # move left
                        if position == 2:
                            position = 1
                        elif position == 3:
                            position = 2
                    elif hex(key) == "0x231": # move right
                        if position == 1:
                            position = 2
                        elif position == 2:
                            position = 3
                    win.set_position(position, screen)
                    rewrite_all_wins(env)
        except Exception as err:
            log("brows menu | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env, None

