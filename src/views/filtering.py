import curses
import curses.ascii
import traceback

from views.help import show_help

from modules.buffer import UserInput
from modules.directory import Filter

from utils.printing import *
from utils.logger import *


def filter_management(stdscr, screen, win, env):
    curses.curs_set(1)

    user_input = UserInput()
    if env.is_brows_mode() and env.path_filter_on():
        user_input.text = list(env.filter.path)
    elif env.is_view_mode() and env.content_filter_on():
        user_input.text = list(env.filter.content)
    elif env.is_tag_mode() and env.tag_filter_on():
        user_input.text = list(env.filter.tag)


    if not env.filter:
        project_path = env.get_project_path()
        env.filter = Filter(project_path)

    old_filter_text = ''.join(user_input.text)

    print_hint(env, filter_mode=True)

    while True:
        try:

            """ show user input """
            max_cols = win.end_x - win.begin_x + win.line_num_shift
            max_rows = win.end_y - win.begin_y - 1
            show_filter(screen, user_input, max_rows, max_cols, env)

            shifted_pointer = user_input.get_shifted_pointer()
            new_row, new_col = win.last_row, win.begin_x+1-win.border+shifted_pointer
            if env.line_numbers and env.is_view_mode():
                new_col -= win.line_num_shift
            stdscr.move(new_row, new_col)


            key = stdscr.getch()

            if key == curses.ascii.ESC: # exit filter management
                return env
            elif key == curses.KEY_F10:
                env.set_exit_mode()
                return env
            elif key == curses.KEY_RESIZE:
                env = resize_all(stdscr, env)
                screen, win = env.get_screen_for_current_mode()
            elif key == curses.KEY_F8: # remove all filters
                # env.filter.reset_by_current_mode(env)
                env.filter.reset_all()
                env.filter.find_files(env)
                env.prepare_browsing_after_filter()
                return env
            elif key == curses.KEY_F1: # help
                show_help(stdscr, env, filter_mode=True)
                curses.curs_set(1)
            # ============ edit user input ============
            elif key == curses.KEY_LEFT:
                user_input.left(win)
            elif key == curses.KEY_RIGHT:
                user_input.right(win)
            elif key == curses.KEY_DOWN:
                end_of_input = len(user_input)
                user_input.pointer = end_of_input
                user_input.horizontal_shift(win)
            elif key == curses.KEY_UP:
                user_input.pointer = 0
                user_input.col_shift = 0
            elif key == curses.KEY_DC:
                user_input.delete_symbol(win)
            elif key == curses.KEY_BACKSPACE:
                if user_input.pointer > 0:
                    user_input.left(win)
                    user_input.delete_symbol(win)
            elif curses.ascii.isprint(key):
                user_input.insert_symbol(win, chr(key))
            elif key == curses.ascii.NL: # enter filter
                text = ''.join(user_input.text)
                env.filter.add_by_current_mode(env, text)
                env.filter.find_files(env)
                if old_filter_text != text:
                    env.prepare_browsing_after_filter()
                return env
        except Exception as err:
            log("filter management | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env
