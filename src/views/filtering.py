import curses
import curses.ascii
import traceback

from controls.control import *

from views.help import show_help

from modules.buffer import UserInput
from modules.directory import Filter

from utils.screens import *
from utils.printing import *
from utils.logger import *



def filter_management(stdscr, screen, win, env):
    curses.curs_set(1)

    env.filter_mode = True

    user_input = UserInput()
    if env.is_brows_mode() and env.path_filter_on():
        user_input.text = list(env.filter.path)
    elif env.is_view_mode() and env.content_filter_on():
        user_input.text = list(env.filter.content)
    elif env.is_tag_mode() and env.tag_filter_on():
        user_input.text = list(env.filter.tag)


    if not env.filter:
        # project_path = env.get_project_path()
        project_path = env.cwd.proj_conf_path
        env.filter = Filter(project_path)

    old_filter_text = ''.join(user_input.text)

    print_hint(env)

    filter_data = (screen, win, user_input)
    
    while True:
        screen, win, user_input = filter_data

        """ show user input """
        max_cols = win.end_x - win.begin_x + win.line_num_shift
        max_rows = win.end_y - win.begin_y - 1
        show_filter(screen, user_input, max_rows, max_cols, env)

        try:
            """ move cursor to correct position """
            shifted_pointer = user_input.get_shifted_pointer()
            new_row, new_col = win.last_row, win.begin_x+1-win.border+shifted_pointer
            if env.line_numbers and env.is_view_mode():
                new_col -= win.line_num_shift
            stdscr.move(new_row, new_col)
        except Exception as err:
            log("filter move cursor | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            env.filter_mode = False
            return env


        key = stdscr.getch()

        try:
            function = get_function_for_key(env, key)
            if function is not None:
                filter_data = (screen, win, user_input)
                filter_data, env, exit_program = run_function(stdscr, filter_data, old_filter_text, env, function, key)
                if exit_program:
                    env.filter_mode = False
                    return env

        except Exception as err:
            log("filter management | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            env.filter_mode = False
            return env



""" implementation of functions for filter management """
def run_function(stdscr, filter_data, old_filter_text, env, fce, key):
    screen, win, user_input = filter_data

    # ======================= EXIT =======================
    if fce == EXIT_PROGRAM:
        env.set_exit_mode()
        return filter_data, env, True
    elif fce == EXIT_FILTER:
        return filter_data, env, True
    # ======================= RESIZE =======================
    elif fce == RESIZE_WIN:
        env = resize_all(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
        rewrite_all_wins(env)
    # ======================= SHOW HELP =======================
    elif fce == SHOW_HELP:
        show_help(stdscr, env)
        curses.curs_set(1)
    # ======================= ARROWS =======================
    elif fce == CURSOR_UP:
        user_input.pointer = 0
        user_input.col_shift = 0
    elif fce == CURSOR_DOWN:
        end_of_input = len(user_input)
        user_input.pointer = end_of_input
        user_input.horizontal_shift(win)
    elif fce == CURSOR_LEFT:
        user_input.left(win)
    elif fce == CURSOR_RIGHT:
        user_input.right(win)
    # ======================= EDIT FILTER =======================
    elif fce == DELETE:
        user_input.delete_symbol(win)
    elif fce == BACKSPACE:
        if user_input.pointer > 0:
            user_input.left(win)
            user_input.delete_symbol(win)
    elif fce == PRINT_CHAR:
        user_input.insert_symbol(win, chr(key))
    elif fce == SAVE_FILTER:
        text = ''.join(user_input.text)
        env.filter.add_by_current_mode(env, text)
        env.filter.find_files(env)
        if old_filter_text != text:
            env.prepare_browsing_after_filter()
        return filter_data, env, True
    # ======================= REMOVE FILTER =======================
    elif fce == REMOVE_FILTER:
        # env.filter.reset_by_current_mode(env)
        env.filter.reset_all()
        env.filter.find_files(env)
        env.prepare_browsing_after_filter()
        return filter_data, env, True


    result_data = (screen, win, user_input)
    return result_data, env, False
