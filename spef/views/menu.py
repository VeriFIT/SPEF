import curses
import curses.ascii
import traceback

import spef.controls.functions as func
from spef.utils.coloring import COL_GREEN
from spef.controls.control import get_function_for_key
from spef.utils.printing import rewrite_all_wins, show_menu
from spef.utils.screens import resize_all
from spef.utils.logger import log
from spef.views.help import show_help


"""
menu_options = []
returns env, selected_options
"""


def brows_menu(
    stdscr, env, menu_options, keys=False, select_multiple=False, color=None, title=None
):
    curses.curs_set(0)

    env.menu_mode = True

    if color is None:
        color = curses.color_pair(COL_GREEN)

    screen, win = env.get_center_win(reset=True, row=0, col=0)
    win.set_border(0)

    rewrite_all_wins(env)

    selected_options = []
    keys_list = None
    if keys:
        keys_list = [str(i) for i in "123456789"]
        keys_list.extend([str(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"])

    menu_data = (keys_list, menu_options, select_multiple)

    while True:
        screen, win = env.get_center_win()

        """ show menu options """
        show_menu(
            screen,
            win,
            menu_options,
            env,
            keys=keys_list,
            selected=selected_options,
            color=color,
            title=title,
        )

        key = stdscr.getch()

        try:
            function = get_function_for_key(env, key)
            if function is not None:
                selected_options, env, exit_program = run_function(
                    stdscr, menu_data, selected_options, env, function, key
                )
                if exit_program:
                    env.menu_mode = False
                    return env, selected_options

        except Exception as err:
            log("brows menu | " + str(err) + " | " + str(traceback.format_exc()))
            env.set_exit_mode()
            return env, None


""" implementation of functions for browsing in menu """


def run_function(stdscr, menu_data, selected_options, env, fce, key):
    screen, win = env.get_center_win()
    old_position = win.position

    keys_list, menu_options, select_multiple = menu_data

    # ======================= EXIT =======================
    if fce == func.EXIT_PROGRAM:
        rewrite_all_wins(env)
        env.set_exit_mode()
        return None, env, True
    elif fce == func.EXIT_MENU:
        rewrite_all_wins(env)
        return None, env, True
    # ======================= RESIZE =======================
    elif fce == func.RESIZE_WIN:
        old_shift, old_row = win.row_shift, win.cursor.row - win.row_shift
        env = resize_all(stdscr, env)
        screen, win = env.get_center_win(reset=True, row=0, col=0)
        new_row = max(min(old_row, win.end_y - win.begin_y - win.border - 2), 0)
        win.set_cursor(new_row + old_shift, 0)
        win.row_shift = old_shift
        win.set_border(0)
        rewrite_all_wins(env)
    # ======================= SHOW HELP =======================
    elif fce == func.SHOW_HELP:
        show_help(stdscr, env)
        curses.curs_set(1)
    # ========================= ARROWS =========================
    elif fce == func.CURSOR_UP:
        win.up(menu_options, use_restrictions=False)
    elif fce == func.CURSOR_DOWN:
        win.down(menu_options, use_restrictions=False)
    # ====================== SELECT OPTION ======================
    elif fce == func.SAVE_OPTION:
        if select_multiple:
            return selected_options, env, True
        else:
            option = win.cursor.row
            return option, env, True
    elif fce == func.SELECT_BY_IDX:
        if keys_list is not None:
            char_key = chr(key)
            if char_key in keys_list:
                if char_key in [str(i) for i in "123456789"]:
                    option = int(char_key) - 1
                    if select_multiple:
                        selected_options.append(option)
                    else:
                        return option, env, True
                elif char_key in [str(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]:
                    option = ord(char_key) - 55 - 1
                    if select_multiple:
                        selected_options.append(option)
                    else:
                        return option, env, True
    elif fce == func.SELECT_OPTION:
        if select_multiple:
            option = win.cursor.row
            selected_options.append(option)
    # ========================= MOVE WIN =========================
    elif fce == func.MOVE_LEFT:
        if old_position == 2:
            win.set_position(1, screen)
        elif old_position == 3:
            win.set_position(2, screen)
        rewrite_all_wins(env)
    elif fce == func.MOVE_RIGHT:
        if old_position == 1:
            win.set_position(2, screen)
        elif old_position == 2:
            win.set_position(3, screen)
        rewrite_all_wins(env)

    env.update_center_win(win)
    return selected_options, env, False
