import curses
import curses.ascii


from config import Config
from directory import Directory
from window import Window, Cursor
from printing import *
from logger import *



def refresh_main_screens(stdscr, config):
    stdscr.erase()
    config.left_screen.border(0)
    config.right_screen.border(0)
    config.down_screen.border(0)

    stdscr.refresh()
    config.left_screen.refresh()
    config.right_screen.refresh()
    config.down_screen.refresh()


def resize_win(win, line_numbers):
    new_shift = len(line_numbers)+1

    shift = win.line_num_shift
    border = win.border
    begin_y = win.begin_y - win.border
    begin_x = win.begin_x - win.border - shift
    height = win.end_y - win.begin_y + 1
    width = win.end_x - win.begin_x + 1 + shift

    win = Window(height, width-new_shift, begin_y, begin_x+new_shift, border=border, line_num_shift=new_shift)
    return win


def resize_all(stdscr, conf, force_resize=False):
    """ get cursor positions from old windows """
    l_win_old_row, l_win_old_col = conf.left_win.get_cursor_position()
    rd_win_old_row, rd_win_old_col = conf.right_down_win.get_cursor_position()

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

            """ set new cursor positions to windows """
            l_win_new_row = min(l_win_old_row, new_conf.left_win.end_y-2)
            l_win_new_col = min(l_win_old_col, new_conf.left_win.end_x)
            rd_win_new_row = min(rd_win_old_row, new_conf.right_down_win.end_y-2)
            rd_win_new_col = min(rd_win_old_col, new_conf.right_down_win.end_x)
            new_conf.left_win.set_cursor(l_win_new_row, l_win_new_col)
            new_conf.right_down_win.set_cursor(rd_win_new_row, rd_win_new_col)

            # TODO: cursor stays in the middle (see window resizing in vim)
            new_conf.right_win.set_cursor(new_conf.right_win.begin_y, new_conf.right_win.begin_x)

            """ rewrite all screens """
            print_hint(new_conf)
            show_directory_content(new_conf.left_screen, new_conf.left_win, new_conf.cwd, new_conf)
            if new_conf.edit_allowed:
                show_file_content(new_conf.right_screen, new_conf.right_win, new_conf.buffer, new_conf.report, new_conf)
            else:
                show_file_content(new_conf.right_up_screen, new_conf.right_up_win, new_conf.buffer, new_conf.report, new_conf)
                show_tags(new_conf.right_down_screen, new_conf.right_down_win, new_conf.tags, new_conf)
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
    else:
        config = Config(screens["LS"], screens["RS"], screens["DS"], screens["CS"])

    config.right_up_screen = screens["RUS"]
    config.right_down_screen = screens["RDS"]

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
