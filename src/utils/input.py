
import curses
import curses.ascii


from modules.directory import Directory
from modules.window import Window
from modules.buffer import UserInput


from utils.printing import *
from utils.screens import *
from utils.logger import *


ESC = 27


def get_user_input(stdscr, env, title=None, user_input=None):
    curses.curs_set(1)

    screen, win = env.get_center_win(reset=True)
    position = win.position

    if user_input is None:
        user_input = UserInput()

    rewrite_all_wins(stdscr, env)

    while True:
        """ show user input """
        max_cols = win.end_x - win.begin_x - 1
        max_rows = win.end_y - win.begin_y - 1
        color = curses.color_pair(TAG_MGMT)


        """ move cursor to correct position """
        row, col = show_user_input(stdscr, screen, win, user_input, env, color=color, title=title)
        stdscr.move(win.begin_y + row, win.begin_x + col)


        key = stdscr.getch()

        try:
            # ======================= EXIT =======================
            if key == curses.KEY_F1 or key == ESC:
                rewrite_all_wins(stdscr, env)
                return env, None
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                env = resize_all(stdscr, env)
                screen, win = env.get_center_win()
                win.reset()
                win.set_position(position, screen)
                rewrite_all_wins(stdscr, env)
            # ======================= INPUT =======================
            elif key == curses.KEY_LEFT:
                user_input.left(win)
            elif key == curses.KEY_RIGHT:
                user_input.right(win)
            elif key == curses.KEY_DOWN:
                pass
                # end_of_input = len(user_input)
                # user_input.pointer = end_of_input
                # user_input.horizontal_shift(win)
            elif key == curses.KEY_UP:
                pass
                # user_input.pointer = 0
                # user_input.col_shift = 0
            elif key == curses.KEY_DC:
                user_input.delete_symbol(win)
            elif key == curses.KEY_BACKSPACE:
                if user_input.pointer > 0:
                    user_input.left(win)
                    user_input.delete_symbol(win)
            elif key == curses.ascii.NL:
                rewrite_all_wins(stdscr, env)
                return env, user_input.text
            elif curses.ascii.isprint(key):
                user_input.insert_symbol(win, chr(key))
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
                    rewrite_all_wins(stdscr, env)
        except Exception as err:
            log("user input | "+str(err))
            env.set_exit_mode()
            return env, None

