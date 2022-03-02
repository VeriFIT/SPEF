import curses
import curses.ascii
import traceback

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
    b_win_old_row, b_win_old_col = env.windows.brows.get_cursor_position()
    n_win_old_row, n_win_old_col = env.windows.notes.get_cursor_position()
    t_win_old_row, t_win_old_col = env.windows.tag.get_cursor_position()
    
    v_win_old_row = env.windows.view.cursor.row
    v_win_old_col = env.windows.view.cursor.col - env.windows.view.begin_x
    e_win_old_row = env.windows.edit.cursor.row
    e_win_old_col = env.windows.edit.cursor.col - env.windows.edit.begin_x

    """ shift """
    v_win_old_shift = env.windows.view.row_shift
    e_win_old_shift = env.windows.edit.row_shift

    v_win_old_tab_shift = env.windows.view.tab_shift
    e_win_old_tab_shift = env.windows.edit.tab_shift

    """ height """
    v_win_old_height = env.windows.view.end_y - env.windows.view.begin_y - 1
    e_win_old_height = env.windows.edit.end_y - env.windows.edit.begin_y - 1


    result_env = env
    try:
        if curses.is_term_resized(curses.LINES,curses.COLS) or force_resize:
            """ screen resize """
            y,x = stdscr.getmaxyx()
            stdscr.clear()
            if curses.is_term_resized(curses.LINES,curses.COLS):
                curses.resizeterm(y,x)
            stdscr.refresh()

            """ create screens with new size """
            screens, windows = create_screens_and_windows(y, x, env.line_numbers)
            windows.set_edges(env.win_left_edge, env.win_right_edge, env.win_top_edge, env.win_bottom_edge)

            new_env = env
            new_env.screens = screens
            new_env.windows = windows

            """ set old cursor positions to resized windows """
            b_win_new_row = min(b_win_old_row, new_env.windows.brows.end_y-2)
            b_win_new_col = min(b_win_old_col, new_env.windows.brows.end_x)
            n_win_new_row = min(n_win_old_row, new_env.windows.notes.end_y-2)
            n_win_new_col = min(n_win_old_col, new_env.windows.notes.end_x)
            t_win_new_row = min(t_win_old_row, new_env.windows.tag.end_y-2)
            t_win_new_col = min(t_win_old_col, new_env.windows.tag.end_x)

            v_win_new_col = v_win_old_col + new_env.windows.view.begin_x
            e_win_new_col = e_win_old_col + new_env.windows.edit.begin_x

            new_env.windows.brows.set_cursor(b_win_new_row, b_win_new_col)
            new_env.windows.notes.set_cursor(n_win_new_row, n_win_new_col)
            new_env.windows.tag.set_cursor(t_win_new_row, t_win_new_col)
            new_env.windows.view.set_cursor(v_win_old_row, v_win_new_col)
            new_env.windows.edit.set_cursor(e_win_old_row, e_win_new_col)

            new_env.windows.view.tab_shift = v_win_old_tab_shift
            new_env.windows.edit.tab_shift = e_win_old_tab_shift


            """ set old shift to resized windows - cursor stays in the middle """
            v_win_height = new_env.windows.view.end_y - new_env.windows.view.begin_y - 1
            e_win_height = new_env.windows.edit.end_y - new_env.windows.edit.begin_y - 1
            
            v_win_new_shift = new_vertical_shift(v_win_old_shift, v_win_old_height, v_win_old_row, v_win_height)
            e_win_new_shift = new_vertical_shift(e_win_old_shift, e_win_old_height, e_win_old_row, e_win_height)

            new_env.windows.view.row_shift = v_win_new_shift
            new_env.windows.edit.row_shift = e_win_new_shift


            result_env = new_env
    except Exception as err:
        log("resizing | "+str(err)+" | "+str(traceback.format_exc()))
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
    center_win = Window(c_win_h, c_win_w, c_win_y, c_win_x, border=1)
    brows_win = Window(l_win_h, l_win_w, l_win_y, l_win_x)
    notes_win = Window(l_win_h, l_win_w, l_win_y, l_win_x)
    tag_win = Window(right_down_h, r_win_w, r_win_y+right_up_h, r_win_x)

    #  OPTION A : note highlight on full line
    # shift = 0 if line_numbers is None else len(line_numbers)+1 # +1 stands for a space between line number and text
    #  OPTION B : note highlight on line number
    #  OPTION C : note highlight on symbol '|' before line
    shift = 1 if line_numbers is None else len(line_numbers)+1 # +1 stands for a space between line number and text
    edit_win = Window(r_win_h, r_win_w-shift, r_win_y, r_win_x+shift, border=1, line_num_shift=shift) # +1 stands for bordes at first line and col
    view_win = Window(right_up_h, r_win_w-shift, r_win_y, r_win_x+shift, border=1, line_num_shift=shift)


    """ set background color for screens """
    bkgd_col = curses.color_pair(BKGD)
    left_screen.bkgd(' ', bkgd_col)
    right_screen.bkgd(' ', bkgd_col)
    down_screen.bkgd(' ', bkgd_col)
    center_screen.bkgd(' ', bkgd_col)
    right_up_screen.bkgd(' ', bkgd_col)
    right_down_screen.bkgd(' ', bkgd_col)

    screens = Screens(left_screen, right_screen, down_screen, center_screen, right_up_screen, right_down_screen)
    windows = Windows(brows_win, edit_win, center_win, view_win, tag_win, notes_win)

    return screens, windows

