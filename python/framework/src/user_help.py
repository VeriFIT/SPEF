
import curses
import curses.ascii


from directory import Directory
from window import Window
from buffer import UserInput
from screens import *
from printing import *
from logger import *


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
            rewrite_all_wins(stdscr, conf)
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
                rewrite_all_wins(stdscr, conf)


def rewrite_all_wins(stdscr, conf):
    refresh_main_screens(stdscr, conf)
    cwd = Directory(conf.filter.project_path, files=conf.filter.files) if conf.filter_not_empty() else conf.cwd
    show_directory_content(conf.left_screen, conf.left_win, cwd, conf)

    view_screen = conf.right_screen if conf.edit_allowed else conf.right_up_screen
    view_win = conf.right_win if conf.edit_allowed else conf.right_up_win
    show_file_content(view_screen, view_win, conf.buffer, conf.report, conf, None)
    if not conf.edit_allowed and conf.tags:
        show_tags(conf.right_down_screen, conf.right_down_win, conf.tags, conf)
