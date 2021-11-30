import curses
import curses.ascii

from user_help import show_help

from buffer import UserInput
from directory import Filter
from printing import *
from logger import *

def filter_management(stdscr, screen, win, conf):
    curses.curs_set(1)

    user_input = UserInput()
    if conf.is_brows_mode() and conf.path_filter_on():
        user_input.text = list(conf.filter.path)
    elif conf.is_view_mode() and conf.content_filter_on():
        user_input.text = list(conf.filter.content)
    elif conf.is_tag_mode() and conf.tag_filter_on():
        user_input.text = list(conf.filter.tag)


    if not conf.filter:
        project_path = conf.get_project_path()
        conf.filter = Filter(project_path)

    print_hint(conf, filter_mode=True)

    while True:
        try:

            """ show user input """
            max_cols = win.end_x - win.begin_x
            max_rows = win.end_y - win.begin_y - 1
            show_filter(screen, user_input, max_rows, max_cols, conf)

            shifted_pointer = user_input.get_shifted_pointer()
            new_row, new_col = win.last_row, win.begin_x+1-win.border+shifted_pointer
            if conf.line_numbers and conf.is_view_mode():
                new_col -= win.line_num_shift
            stdscr.move(new_row, new_col)


            key = stdscr.getch()

            if key in (curses.ascii.ESC, curses.KEY_F10): # exit filter management
                user_input.reset()
                curses.curs_set(0)
                return conf
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen, win = conf.get_screen_for_current_mode()
            elif key == curses.KEY_F8: # remove all filters
                # conf.filter.reset_by_current_mode(conf)
                conf.filter.reset_all()
                conf.filter.find_files(conf)
                user_input.reset()
                curses.curs_set(0)
                return conf
            elif key == curses.KEY_F1: # help
                show_help(stdscr, conf, filter_mode=True)
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
                conf.filter.add_by_current_mode(conf, text)
                conf.filter.find_files(conf)
                user_input.reset()
                curses.curs_set(0)
                return conf
        except Exception as err:
            log("filter management | "+str(err))
            conf.set_exit_mode()
            return conf
