import curses
import curses.ascii
import traceback

from spef.utils.coloring import COL_GREEN
import spef.controls.functions as func
from spef.controls.control import get_function_for_key
from spef.modules.buffer import UserInput
from spef.utils.printing import rewrite_all_wins, show_user_input
from spef.utils.screens import resize_all
from spef.utils.logger import log
from spef.views.help import show_help


def get_user_input(stdscr, env, title=None, user_input=None):
    env.user_input_mode = True

    screen, win = env.get_center_win(reset=True)

    if user_input is None:
        user_input = UserInput()

    rewrite_all_wins(env)
    curses.curs_set(1)

    while True:
        screen, win = env.get_center_win()

        """ show user input """
        max_cols = win.end_x - win.begin_x - 1
        max_rows = win.end_y - win.begin_y - 1
        color = curses.color_pair(COL_GREEN)

        """ move cursor to correct position """
        row, col = show_user_input(
            screen, user_input, max_rows, max_cols, env, color=color, title=title
        )
        stdscr.move(win.begin_y + row, win.begin_x + col)

        key = stdscr.getch()

        try:
            function = get_function_for_key(env, key)
            if function is not None:
                user_input, env, exit_program = run_function(
                    stdscr, user_input, env, function, key
                )
                if exit_program:
                    env.user_input_mode = False
                    return env, user_input.text

        except Exception as err:
            log("user input | " + str(err) + " | " + str(traceback.format_exc()))
            env.set_exit_mode()
            return env, None


""" implementation of functions for user input """


def run_function(stdscr, user_input, env, fce, key):
    screen, win = env.get_center_win()
    old_position = win.position

    # ======================= EXIT =======================
    if fce == func.EXIT_PROGRAM:
        rewrite_all_wins(env)
        env.set_exit_mode()
        user_input.text = None
        return user_input, env, True
    elif fce == func.EXIT_USER_INPUT:
        rewrite_all_wins(env)
        user_input.text = None
        return user_input, env, True
    # ======================= RESIZE =======================
    elif fce == func.RESIZE_WIN:
        env = resize_all(stdscr, env)
        screen, win = env.get_center_win()
        win.reset()
        win.set_position(old_position, screen)
        rewrite_all_wins(env)
        curses.curs_set(1)
    # ======================= SHOW HELP =======================
    elif fce == func.SHOW_HELP:
        show_help(stdscr, env)
        curses.curs_set(1)
    # ========================= ARROWS =========================
    elif fce == func.CURSOR_UP:  # TODO: Fix
        user_input.pointer = 0
        user_input.col_shift = 0
    elif fce == func.CURSOR_DOWN:  # TODO: Fix
        end_of_input = len(user_input)
        user_input.pointer = end_of_input
        user_input.horizontal_shift(win)
    elif fce == func.CURSOR_LEFT:
        user_input.left(win)
    elif fce == func.CURSOR_RIGHT:
        user_input.right(win)
    # ======================== INPUT ========================
    elif fce == func.DELETE_CHAR:
        user_input.delete_symbol(win)
    elif fce == func.BACKSPACE_CHAR:
        if user_input.pointer > 0:
            user_input.left(win)
            user_input.delete_symbol(win)
    elif fce == func.SAVE_INPUT:
        rewrite_all_wins(env)
        return user_input, env, True
    elif fce == func.PRINT_CHAR:
        user_input.insert_symbol(win, chr(key))
    # ========================= MOVE WIN =========================
    elif fce == func.MOVE_LEFT:
        if old_position == 2:
            win.set_position(1, screen)
        elif old_position == 3:
            win.set_position(2, screen)
        rewrite_all_wins(env)
        curses.curs_set(1)
    elif fce == func.MOVE_RIGHT:
        if old_position == 1:
            win.set_position(2, screen)
        elif old_position == 2:
            win.set_position(3, screen)
        rewrite_all_wins(env)
        curses.curs_set(1)

    env.update_center_win(win)
    return user_input, env, False
