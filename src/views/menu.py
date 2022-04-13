
import curses
import curses.ascii
import traceback

from controls.control import *

from modules.directory import Directory
from modules.window import Window
from modules.buffer import UserInput

from utils.printing import *
from utils.screens import *
from utils.logger import *


"""
menu_options = []
returns env, option
"""
def brows_menu(stdscr, env, menu_options, keys=False, color=None, title=None):
    curses.curs_set(0)

    env.menu_mode = True

    if color is None:
        color = curses.color_pair(COL_TITLE)

    screen, win = env.get_center_win(reset=True, row=0, col=0)
    win.set_border(0)

    rewrite_all_wins(env)

    keys_list = None
    if keys:
        keys_list = [str(i) for i in "123456789"]
        keys_list.extend([str(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"])

    while True:
        screen, win = env.get_center_win()

        """ show menu options """
        max_cols = win.end_x - win.begin_x - 1
        max_rows = win.end_y - win.begin_y - 1

        show_menu(screen, win, menu_options, max_rows, max_cols, env, keys=keys_list, color=color, title=title)

        key = stdscr.getch()

        try:
            function = get_function_for_key(env, key)
            if function is not None:
                option, env, exit_program = run_function(stdscr, keys_list, menu_options, env, function, key)
                if exit_program:
                    env.menu_mode = False
                    return env, option

        except Exception as err:
            log("brows menu | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env, None



""" implementation of functions for browsing in menu """
def run_function(stdscr, keys_list, menu_options, env, fce, key):
    screen, win = env.get_center_win()
    old_position = win.position

    option = None

    # ======================= EXIT =======================
    if fce == EXIT_PROGRAM:
        rewrite_all_wins(env)
        env.set_exit_mode()
        return option, env, True
    elif fce == EXIT_MENU:
        rewrite_all_wins(env)
        return option, env, True
    # ======================= RESIZE =======================
    elif fce == RESIZE_WIN:
        old_shift, old_row = win.row_shift, win.cursor.row - win.row_shift
        env = resize_all(stdscr, env)
        screen, win = env.get_center_win(reset=True, row=0, col=0)
        new_row = max(min(old_row, win.end_y-win.begin_y-win.border-2), 0)
        win.set_cursor(new_row+old_shift, 0)
        win.row_shift = old_shift
        win.set_border(0)
        rewrite_all_wins(env)
    # ======================= SHOW HELP =======================
    # elif fce == SHOW_HELP:
    #     show_help(stdscr, env)
    #     curses.curs_set(1)
    # ========================= ARROWS =========================
    elif fce == CURSOR_UP:
        win.up(menu_options, use_restrictions=False)
    elif fce == CURSOR_DOWN:
        win.down(menu_options, use_restrictions=False)
    # ====================== SELECT OPTION ====================== 
    elif fce == SAVE_OPTION:
        option = win.cursor.row
        return option, env, True
    elif fce == SELECT_BY_IDX:
        if keys_list is not None:
            char_key = chr(key)
            if char_key in keys_list:
                if char_key in [str(i) for i in "123456789"]:
                    option = int(char_key)-1
                    return option, env, True
                elif char_key in [str(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]:
                    option = ord(char_key)-55-1
                    return option, env, True
    # ========================= MOVE WIN ========================= 
    elif fce == MOVE_LEFT:
        if old_position == 2:
            win.set_position(1, screen)
        elif old_position == 3:
            win.set_position(2, screen)
        rewrite_all_wins(env)
    elif fce == MOVE_RIGHT:
        if old_position == 1:
            win.set_position(2, screen)
        elif old_position == 2:
            win.set_position(3, screen)
        rewrite_all_wins(env)

    env.update_center_win(win)
    return option, env, False

