import curses
import curses.ascii

from config import Config

from modules.directory import Directory
from modules.window import Window, Cursor

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


def resize_all(stdscr, conf, force_resize=False):
    """ get cursor positions from old windows """
    l_win_old_row, l_win_old_col = conf.left_win.get_cursor_position()
    rd_win_old_row, rd_win_old_col = conf.right_down_win.get_cursor_position()

    """ cursor """
    ru_win_old_row = conf.right_up_win.cursor.row
    r_win_old_row = conf.right_win.cursor.row
    """ shift """
    r_win_old_shift = conf.right_win.row_shift
    ru_win_old_shift = conf.right_up_win.row_shift
    """ height """
    ru_win_old_height = conf.right_up_win.end_y - conf.right_up_win.begin_y - 1
    r_win_old_height = conf.right_win.end_y - conf.right_win.begin_y - 1


    result_conf = conf
    try:
        if curses.is_term_resized(curses.LINES,curses.COLS) or force_resize:
            """ screen resize """
            y,x = stdscr.getmaxyx()
            stdscr.clear()
            curses.resizeterm(y,x)
            stdscr.refresh()

            """ create screens with new size """
            screens, windows = create_screens_and_windows(y, x, conf.line_numbers)
            new_conf = create_config(screens, windows, conf)

            """ set old cursor positions to resized windows """
            l_win_new_row = min(l_win_old_row, new_conf.left_win.end_y-2)
            l_win_new_col = min(l_win_old_col, new_conf.left_win.end_x)
            rd_win_new_row = min(rd_win_old_row, new_conf.right_down_win.end_y-2)
            rd_win_new_col = min(rd_win_old_col, new_conf.right_down_win.end_x)
            new_conf.left_win.set_cursor(l_win_new_row, l_win_new_col)
            new_conf.right_down_win.set_cursor(rd_win_new_row, rd_win_new_col)

            # TODO: cursor stays in the middle (see window resizing in vim)
            """ set old shift to resized windows """
            ru_win_height = new_conf.right_up_win.end_y - new_conf.right_up_win.begin_y - 1
            r_win_height = new_conf.right_win.end_y - new_conf.right_win.begin_y - 1
            
            ru_win_new_shift = new_vertical_shift(ru_win_old_shift, ru_win_old_height, ru_win_old_row, ru_win_height)
            r_win_new_shift = new_vertical_shift(r_win_old_shift, r_win_old_height, r_win_old_row, r_win_height)

            new_conf.right_up_win.row_shift = ru_win_new_shift
            new_conf.right_win.row_shift = r_win_new_shift

            new_conf.right_up_win.set_cursor(ru_win_old_row, new_conf.right_up_win.begin_x)
            new_conf.right_win.set_cursor(r_win_old_row, new_conf.right_win.begin_x)

            result_conf = new_conf
    except Exception as err:
        log("resizing | "+str(err))
    finally:
        return result_conf


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


    left_screen = curses.newwin(l_win_h, l_win_w, l_win_y, l_win_x) # browsing
    right_screen = curses.newwin(r_win_h, r_win_w, r_win_y, r_win_x) # editing
    down_screen = curses.newwin(d_win_h, d_win_w, d_win_y, d_win_x) # hint
    center_screen = curses.newwin(c_win_h, c_win_w, c_win_y, c_win_x) # help, menu

    right_up_h = int(r_win_h / 2) + int(r_win_h % 2 != 0)
    right_down_h = int(r_win_h / 2)

    right_up_screen = curses.newwin(right_up_h, r_win_w, r_win_y, r_win_x)
    right_down_screen = curses.newwin(right_down_h, r_win_w, r_win_y + right_up_h, r_win_x)

    if line_numbers is None:
        right_win = Window(r_win_h, r_win_w, r_win_y, r_win_x, border=1) # +1 stands for bordes at first line and col
        right_up_win = Window(right_up_h, r_win_w, r_win_y, r_win_x, border=1)
    else:
        shift = len(line_numbers)+1 # +1 stands for a space between line number and text
        right_win = Window(r_win_h, r_win_w-shift, r_win_y, r_win_x+shift, border=1, line_num_shift=shift) # +1 stands for bordes at first line and col
        right_up_win = Window(right_up_h, r_win_w-shift, r_win_y, r_win_x+shift, border=1, line_num_shift=shift)

    center_win = Window(c_win_h, c_win_w, c_win_y, c_win_x)
    left_win = Window(l_win_h, l_win_w, l_win_y, l_win_x)
    right_down_win = Window(right_down_h, r_win_w, r_win_y+right_up_h, r_win_x)

    screens = {"LS":left_screen, "RS":right_screen, "DS":down_screen,
                "RUS":right_up_screen, "RDS":right_down_screen, "CS":center_screen}
    windows = {"LW":left_win, "RW":right_win, "CW":center_win,
                "RUW":right_up_win, "RDW":right_down_win}

    return screens, windows



def create_config(screens, windows, config=None):
    if config:
        config.left_screen = screens["LS"]
        config.right_screen = screens["RS"]
        config.down_screen = screens["DS"]
        config.center_screen = screens["CS"]
        config.right_up_screen = screens["RUS"]
        config.right_down_screen = screens["RDS"]
    else:
        config = Config(screens["LS"], screens["RS"], screens["DS"], screens["CS"], screens["RUS"], screens["RDS"])


    config.right_win = windows["RW"]
    config.left_win = windows["LW"]
    config.center_win = windows["CW"]
    config.right_up_win = windows["RUW"]
    config.right_down_win = windows["RDW"]

    bkgd_col = curses.color_pair(BKGD)
    config.left_screen.bkgd(' ', bkgd_col)
    config.right_screen.bkgd(' ', bkgd_col)
    config.down_screen.bkgd(' ', bkgd_col)
    config.center_screen.bkgd(' ', bkgd_col)
    config.right_up_screen.bkgd(' ', bkgd_col)
    config.right_down_screen.bkgd(' ', bkgd_col)

    return config
