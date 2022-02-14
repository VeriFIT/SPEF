import curses
import curses.ascii

from config import Environment

from modules.directory import Directory
from modules.window import Windows, Screens, Window, Cursor

from utils.printing import *
from utils.logger import *



def new_vertical_shift(old_shift, old_height, cursor, new_height):
    lines_before = cursor - old_shift - 1
    lines_after = (old_shift+old_height) - cursor

    new_shift = old_shift
    if new_height > old_height: # new window is larger
        height_diff = new_height - old_height
        for i in range(height_diff):
            if lines_before < lines_after:
                # reduce shift so that the window extend at the top (not at the bottom)
                new_shift -= 1
                lines_before += 1
            else:
                # shift stays the same so that the window extend at the bottom
                lines_after += 1
        if new_shift < 0:
            new_shift = 0
    elif new_height < old_height: # new window is smaler
        height_diff = old_height - new_height
        for i in range(height_diff):
            if lines_before > lines_after:
                new_shift += 1
                lines_before -= 1
            else:
                lines_after -= 1
    return new_shift


def resize_all(stdscr, env, force_resize=False):
    """ get cursor positions from old windows """
    l_win_old_row, l_win_old_col = env.windows.left.get_cursor_position()
    rd_win_old_row, rd_win_old_col = env.windows.right_down.get_cursor_position()
    # ru_win_old_row, ru_win_old_col = env.windows.right_up.cursor.row, env.windows.right_up.cursor.col
    # r_win_old_row, r_win_old_col = env.windows.right.cursor.row, env.windows.right.cursor.col
    
    ru_win_old_row = env.windows.right_up.cursor.row
    ru_win_old_col = env.windows.right_up.cursor.col - env.windows.right_up.begin_x
    r_win_old_row = env.windows.right.cursor.row
    r_win_old_col = env.windows.right.cursor.col - env.windows.right.begin_x

    """ shift """
    ru_win_old_shift = env.windows.right_up.row_shift
    r_win_old_shift = env.windows.right.row_shift

    ru_win_old_tab_shift = env.windows.right_up.tab_shift
    r_win_old_tab_shift = env.windows.right.tab_shift

    """ height """
    ru_win_old_height = env.windows.right_up.end_y - env.windows.right_up.begin_y - 1
    r_win_old_height = env.windows.right.end_y - env.windows.right.begin_y - 1


    result_env = env
    try:
        if curses.is_term_resized(curses.LINES,curses.COLS) or force_resize:
            """ screen resize """
            y,x = stdscr.getmaxyx()
            stdscr.clear()
            curses.resizeterm(y,x)
            stdscr.refresh()

            """ create screens with new size """
            screens, windows = create_screens_and_windows(y, x, env.line_numbers)
            windows.set_edges(env.win_left_edge, env.win_right_edge, env.win_top_edge, env.win_bottom_edge)

            new_env = env
            new_env.screens = screens
            new_env.windows = windows

            """ set old cursor positions to resized windows """
            l_win_new_row = min(l_win_old_row, new_env.windows.left.end_y-2)
            l_win_new_col = min(l_win_old_col, new_env.windows.left.end_x)
            rd_win_new_row = min(rd_win_old_row, new_env.windows.right_down.end_y-2)
            rd_win_new_col = min(rd_win_old_col, new_env.windows.right_down.end_x)

            ru_win_new_col = ru_win_old_col + new_env.windows.right_up.begin_x
            r_win_new_col = r_win_old_col + new_env.windows.right.begin_x

            new_env.windows.left.set_cursor(l_win_new_row, l_win_new_col)
            new_env.windows.right_down.set_cursor(rd_win_new_row, rd_win_new_col)
            new_env.windows.right_up.set_cursor(ru_win_old_row, ru_win_new_col)
            new_env.windows.right.set_cursor(r_win_old_row, r_win_new_col)

            new_env.windows.right_up.tab_shift = ru_win_old_tab_shift
            new_env.windows.right.tab_shift = r_win_old_tab_shift


            """ set old shift to resized windows - cursor stays in the middle """
            ru_win_height = new_env.windows.right_up.end_y - new_env.windows.right_up.begin_y - 1
            r_win_height = new_env.windows.right.end_y - new_env.windows.right.begin_y - 1
            
            ru_win_new_shift = new_vertical_shift(ru_win_old_shift, ru_win_old_height, ru_win_old_row, ru_win_height)
            r_win_new_shift = new_vertical_shift(r_win_old_shift, r_win_old_height, r_win_old_row, r_win_height)

            new_env.windows.right_up.row_shift = ru_win_new_shift
            new_env.windows.right.row_shift = r_win_new_shift


            result_env = new_env
    except Exception as err:
        log("resizing | "+str(err))
    finally:
        return result_env


def create_screens_and_windows(height, width, line_numbers=None):
    half_height = int(height/2)
    quarter_height = int(height/4)
    half_width = int(width/2)
    quarter_width = int(width/4)
    d_win_lines = 1

    """ set window size and position """
    d_win_h, d_win_w = d_win_lines + 2, width # 2 stands for borders
    l_win_h, l_win_w = height - d_win_h , half_width
    r_win_h, r_win_w = height - d_win_h , half_width
    c_win_h, c_win_w = half_height, half_width

    d_win_y, d_win_x = l_win_h, 0
    l_win_y, l_win_x = 0, 0
    r_win_y, r_win_x = 0, l_win_w
    c_win_y, c_win_x = quarter_height, quarter_width

    right_up_h = int(r_win_h / 2) + int(r_win_h % 2 != 0)
    right_down_h = int(r_win_h / 2)


    """ create screens """
    left_screen = curses.newwin(l_win_h, l_win_w, l_win_y, l_win_x) # browsing
    right_screen = curses.newwin(r_win_h, r_win_w, r_win_y, r_win_x) # editing
    down_screen = curses.newwin(d_win_h, d_win_w, d_win_y, d_win_x) # hint
    center_screen = curses.newwin(c_win_h, c_win_w, c_win_y, c_win_x) # help, menu
    right_up_screen = curses.newwin(right_up_h, r_win_w, r_win_y, r_win_x)
    right_down_screen = curses.newwin(right_down_h, r_win_w, r_win_y + right_up_h, r_win_x)


    """ create windows """
    center_win = Window(c_win_h, c_win_w, c_win_y, c_win_x)
    left_win = Window(l_win_h, l_win_w, l_win_y, l_win_x)
    right_down_win = Window(right_down_h, r_win_w, r_win_y+right_up_h, r_win_x)

    shift = 0 if line_numbers is None else len(line_numbers)+1 # +1 stands for a space between line number and text
    right_win = Window(r_win_h, r_win_w-shift, r_win_y, r_win_x+shift, border=1, line_num_shift=shift) # +1 stands for bordes at first line and col
    right_up_win = Window(right_up_h, r_win_w-shift, r_win_y, r_win_x+shift, border=1, line_num_shift=shift)


    """ set background color for screens """
    bkgd_col = curses.color_pair(BKGD)
    left_screen.bkgd(' ', bkgd_col)
    right_screen.bkgd(' ', bkgd_col)
    down_screen.bkgd(' ', bkgd_col)
    center_screen.bkgd(' ', bkgd_col)
    right_up_screen.bkgd(' ', bkgd_col)
    right_down_screen.bkgd(' ', bkgd_col)

    screens = Screens(left_screen, right_screen, down_screen, center_screen, right_up_screen, right_down_screen)
    windows = Windows(left_win, right_win, center_win, right_up_win, right_down_win)

    return screens, windows

