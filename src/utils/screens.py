import curses
import curses.ascii
import traceback

import array
import fcntl
import termios


from modules.environment import Environment
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
    c_win_old_row, c_win_old_col = env.windows.center.get_cursor_position()

    v_win_old_row = env.windows.view.cursor.row
    v_win_old_col = env.windows.view.cursor.col - env.windows.view.begin_x
    vu_win_old_row = env.windows.view_up.cursor.row
    vu_win_old_col = env.windows.view_up.cursor.col - env.windows.view_up.begin_x

    """ shift """
    v_win_old_shift = env.windows.view.row_shift
    vu_win_old_shift = env.windows.view_up.row_shift

    b_win_old_shift = env.windows.brows.row_shift
    n_win_old_shift = env.windows.notes.row_shift
    t_win_old_shift = env.windows.tag.row_shift

    v_win_old_tab_shift = env.windows.view.tab_shift
    vu_win_old_tab_shift = env.windows.view_up.tab_shift

    """ height """
    v_win_old_height = env.windows.view.end_y - env.windows.view.begin_y - 1
    vu_win_old_height = env.windows.view_up.end_y - env.windows.view_up.begin_y - 1

    b_win_old_height = env.windows.brows.end_y - env.windows.brows.begin_y - 1
    n_win_old_height = env.windows.notes.end_y - env.windows.notes.begin_y - 1
    t_win_old_height = env.windows.tag.end_y - env.windows.tag.begin_y - 1


    result_env = env
    try:
        if curses.is_term_resized(curses.LINES,curses.COLS) or force_resize:
            """ screen resize """
            y,x = stdscr.getmaxyx()
            if curses.is_term_resized(curses.LINES,curses.COLS):
                stdscr.clear()
                curses.resizeterm(y,x)
                stdscr.refresh()

                # resize also bash terminal
                if env.bash_fd:
                    size_buff = array.array('H', [x,y,0,0])
                    fcntl.ioctl(env.bash_fd, termios.TIOCSWINSZ, size_buff, 1)

            """ create screens with new size """
            screens, windows = create_screens_and_windows(y, x, env.line_numbers)
            windows.set_edges(env.win_left_edge, env.win_right_edge, env.win_top_edge, env.win_bottom_edge)

            new_env = env
            new_env.screens = screens
            new_env.windows = windows

            """ set old cursor positions to resized windows """
            b_win_new_row = max(min(b_win_old_row, new_env.windows.brows.end_y-2), 0)
            b_win_new_col = max(min(b_win_old_col, new_env.windows.brows.end_x), 0)
            n_win_new_row = max(min(n_win_old_row, new_env.windows.notes.end_y-2), 0)
            n_win_new_col = max(min(n_win_old_col, new_env.windows.notes.end_x), 0)

            t_end_new_win = new_env.windows.tag.end_y-new_env.windows.tag.begin_y-new_env.windows.tag.border
            t_win_new_row = max(min(t_win_old_row, t_end_new_win-2), 0)
            t_win_new_col = max(min(t_win_old_col, new_env.windows.tag.end_x), 0)
            c_end_new_win = new_env.windows.center.end_y-new_env.windows.center.begin_y-new_env.windows.center.border
            c_win_new_row = max(min(c_win_old_row, c_end_new_win-2), 0)
            c_win_new_col = max(min(c_win_old_col, new_env.windows.center.end_x), 0)


            v_win_new_col = v_win_old_col + new_env.windows.view.begin_x
            vu_win_new_col = vu_win_old_col + new_env.windows.view_up.begin_x

            new_env.windows.brows.set_cursor(b_win_new_row+b_win_old_shift, b_win_new_col)
            new_env.windows.notes.set_cursor(n_win_new_row+n_win_old_shift, n_win_new_col)
            new_env.windows.tag.set_cursor(t_win_new_row+t_win_old_shift, t_win_new_col)
            new_env.windows.center.set_cursor(c_win_new_row, c_win_new_col)
            new_env.windows.view.set_cursor(v_win_old_row, v_win_new_col)
            new_env.windows.view_up.set_cursor(vu_win_old_row, vu_win_new_col)

            new_env.windows.view.tab_shift = v_win_old_tab_shift
            new_env.windows.view_up.tab_shift = vu_win_old_tab_shift

            # log(str(new_env.windows.brows.cursor.row))


            """ set old shift to resized windows - cursor stays in the middle """
            v_win_height = new_env.windows.view.end_y - new_env.windows.view.begin_y - 1
            vu_win_height = new_env.windows.view_up.end_y - new_env.windows.view_up.begin_y - 1
            
            v_win_new_shift = new_vertical_shift(v_win_old_shift, v_win_old_height, v_win_old_row, v_win_height)
            vu_win_new_shift = new_vertical_shift(vu_win_old_shift, vu_win_old_height, vu_win_old_row, vu_win_height)

            new_env.windows.view.row_shift = v_win_new_shift
            new_env.windows.view_up.row_shift = vu_win_new_shift

            new_env.windows.brows.row_shift = b_win_old_shift
            new_env.windows.notes.row_shift = n_win_old_shift
            new_env.windows.tag.row_shift = t_win_old_shift


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
    l_win_h, l_win_w = max(height - d_win_h, 0), half_width
    r_win_h, r_win_w = max(height - d_win_h, 0), half_width
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

    # log("b :"+str(l_win_h))
    # log("v :"+str(right_up_h))
    # log("t :"+str(right_down_h))
    #  OPTION A : note highlight on full line
    # shift = 0 if line_numbers is None else len(line_numbers)+1 # +1 stands for a space between line number and text
    #  OPTION B : note highlight on line number
    #  OPTION C : note highlight on symbol '|' before line
    shift = 1 if line_numbers is None else len(line_numbers)+1 # +1 stands for a space between line number and text
    view_vin = Window(r_win_h, max(r_win_w-shift, 0), r_win_y, r_win_x+shift, border=1, line_num_shift=shift) # +1 stands for bordes at first line and col
    view_up_win = Window(right_up_h, max(r_win_w-shift, 0), r_win_y, r_win_x+shift, border=1, line_num_shift=shift)

    """ set background color for screens """
    bkgd_col = curses.color_pair(COL_BKGD)
    left_screen.bkgd(' ', bkgd_col)
    right_screen.bkgd(' ', bkgd_col)
    down_screen.bkgd(' ', bkgd_col)
    center_screen.bkgd(' ', bkgd_col)
    right_up_screen.bkgd(' ', bkgd_col)
    right_down_screen.bkgd(' ', bkgd_col)

    screens = Screens(left_screen, right_screen, down_screen, center_screen, right_up_screen, right_down_screen)
    windows = Windows(brows_win, view_vin, center_win, view_up_win, tag_win, notes_win)

    return screens, windows

