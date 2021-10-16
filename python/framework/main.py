#!/usr/bin/env python3

import curses
import curses.ascii
import datetime
import os
import sys


from buffer import Buffer
from config import *
from directory import Directory
from window import Window, Cursor

ESC = 27

LOG_FILE = "/home/naty/Others/ncurses/python/framework/log"

BORDER = 2
START_Y = 1
START_X = 1


def log(message):
    day = datetime.date.today()
    time = datetime.datetime.now().strftime("%X")
    with open(LOG_FILE, 'a') as f:
        f.write("{} {} | {}\n".format(day,time,message))


# browsing
B_HELP = {"F1":"help", "F2":"menu", "F3":"view",
            "F4":"edit", "F5":"copy", "F6":"rename",
            "F8":"delete", "F9":"filter", "F10":"exit"}
# editing
E_HELP = {"F1":"help", "F2":"save", "F3":"note",
            "F9":"filter", "F10":"exit"}
# viewing
V_HELP = {"F1":"help", "F5":"goto",
            "F9":"filter", "F10":"exit"}

def print_hint(screen, mode):
    screen.erase()
    screen.border(0)
    size = screen.getmaxyx()

    if mode == BROWSING:
        help_dict = B_HELP
    elif mode == EDITING:
        help_dict = E_HELP
    else:
        help_dict = {}

    string = ""
    for key in help_dict:
        hint = " | " + str(key) + ":" + str(help_dict[key])
        if len(string) + len(hint) <= size[1]:
            string += hint
    screen.addstr(1, 1, string[2:])
    screen.refresh()


def resize_all(stdscr, conf):
    """ get cursor positions from old windows """
    l_win_old_row, l_win_old_col = conf.left_win.get_cursor_position()

    try:
        if curses.is_term_resized(curses.LINES,curses.COLS):
            """ screen resize """
            y,x = stdscr.getmaxyx()
            stdscr.clear()
            curses.resizeterm(y,x)
            stdscr.refresh()

            """ create screens with new size """
            screens, windows = create_screens_and_windows(y, x)
            conf.left_screen = screens["LS"]
            conf.right_screen = screens["RS"]
            conf.down_screen = screens["DS"]

            conf.right_win = windows["RW"]
            conf.left_win = windows["LW"]

            """ set new cursor positions to windows """
            l_win_new_row = min(l_win_old_row, conf.left_win.end_y-2)
            l_win_new_col = min(l_win_old_col, conf.left_win.end_x)
            conf.left_win.set_cursor(l_win_new_row, l_win_new_col)

            # TODO: cursor stays in the middle (see window resizing in vim)
            conf.right_win.set_cursor(conf.right_win.begin_y, conf.right_win.begin_x)

            """ rewrite all screens """
            print_hint(conf.down_screen, conf.mode)
            if conf.mode in (BROWSING, EDITING):
                show_directory_content(conf.left_screen, conf.left_win, conf.cwd, conf.highlight, conf.normal)
                show_file_content(conf.right_screen, conf.right_win, conf.file_buffer, conf.highlight, conf.normal)
            else:
                # TODO
                # in VIEW mode or TAGGING mode
                # show only half file content and tag window
                pass
    except Exception as err:
        log("resizing | "+str(err))
    finally:
        return conf


def create_screens_and_windows(height, width):
    half_width = int(width/2)
    d_win_lines = 1

    """ set window size and position """
    d_win_h, d_win_w = d_win_lines + BORDER, width - START_X
    l_win_h, l_win_w = height - d_win_h - START_Y, half_width
    r_win_h, r_win_w = height - d_win_h - START_Y, half_width - START_X

    d_win_y, d_win_x = START_Y + l_win_h, START_X
    l_win_y, l_win_x = START_Y, START_X
    r_win_y, r_win_x = START_Y, START_X + l_win_w

    left_screen = curses.newwin(l_win_h, l_win_w, l_win_y, l_win_x) # browsing
    right_screen = curses.newwin(r_win_h, r_win_w, r_win_y, r_win_x) # editing
    down_screen = curses.newwin(d_win_h, d_win_w, d_win_y, d_win_x) # hint

    right_win = Window(r_win_h, r_win_w, r_win_y+1, r_win_x+1) # +1 stands for bordes at first line and col
    left_win = Window(l_win_h, l_win_w, 0, 0)

    screens = {"LS":left_screen, "RS":right_screen, "DS":down_screen}
    windows = {"LW":left_win, "RW":right_win}

    return screens, windows


""" ======================= START MAIN ========================= """
def main(stdscr):
    log("START")
    stdscr.clear()
    curses.set_escdelay(1)

    """ set coloring """
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

    highlight = curses.color_pair(1)
    normal = curses.A_NORMAL
    bkgd_col = curses.color_pair(2)

    """ create screen for browsing, editing and showing hint """
    screens, windows = create_screens_and_windows(curses.LINES, curses.COLS)
    left_screen = screens["LS"]
    right_screen = screens["RS"]
    down_screen = screens["DS"]

    """ create config """
    config = Config(left_screen, right_screen, down_screen)
    config.set_coloring(highlight, normal)

    config.right_win = windows["RW"]
    config.left_win = windows["LW"]
    config.left_win.set_cursor(0,0)

    stdscr.bkgd(' ', bkgd_col)
    config.left_screen.bkgd(' ', bkgd_col)
    config.right_screen.bkgd(' ', bkgd_col)
    config.down_screen.bkgd(' ', bkgd_col)

    """ show all screens """
    stdscr.erase()
    config.left_screen.border(0)
    config.right_screen.border(0)
    config.down_screen.border(0)

    stdscr.refresh()
    config.left_screen.refresh()
    config.right_screen.refresh()
    config.down_screen.refresh()


    """ get current files and dirs """
    config.cwd = get_directory_content()

    while True:
        print_hint(config.down_screen,config.mode)
        if config.mode == EXIT:
            # stdscr.getkey()
            break
        elif config.mode == BROWSING:
            config = browsing(stdscr, config)
        elif config.mode == EDITING:
            config = editing(stdscr, config)
            # break
    
    log("END")
""" ======================= END MAIN ========================= """


""" **************************** BROWSING **************************** """
def browsing(stdscr, conf):
    curses.curs_set(0) # set cursor as invisible

    screen = conf.left_screen
    win = conf.left_win
    cwd = conf.cwd

    while True:
        """ print current directory structure """
        show_directory_content(screen, win, cwd, conf.highlight, conf.normal)

        key = stdscr.getch()
        try:
            if key == ESC : # ESC
                conf = config_browsing(conf, win, cwd) # save browsing state before exit browsing
                if quit_program(stdscr, conf):
                    conf.set_exit_mode()
                    return conf
                else:
                    show_directory_content(screen, win, cwd, conf.highlight, conf.normal)
                    continue
            elif key == ord('\t'): # change focus
                conf = config_browsing(conf, win, cwd, EDITING)
                return conf
            elif key == curses.KEY_UP:
                win.up(cwd, use_restrictions=False)
            elif key == curses.KEY_DOWN:
                win.down(cwd, use_restrictions=False)
            elif key == curses.KEY_RIGHT:
                if win.cursor.row < len(cwd.dirs):
                    """ change current directory to subdirectory """
                    os.chdir(os.getcwd()+'/'+cwd.dirs[win.cursor.row])
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0) # set cursor on first position (first item)
            elif key == curses.KEY_LEFT:
                """ change current directory to parent directory """
                current_dir = os.path.basename(os.getcwd()) # get directory name
                if current_dir: # if its not root
                    os.chdir('..')
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0)
                    """ set cursor position to prev directory """
                    dir_position = cwd.dirs.index(current_dir) # find position of prev directory
                    if dir_position:
                        for i in range(0, dir_position):
                            win.down(cwd, use_restrictions=False)
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen = conf.left_screen
                win = conf.left_win

            elif key == curses.KEY_F4: # F4 for edit file
                """ open file to edit and change focus """
                if win.cursor.row >= len(cwd.dirs):
                    conf = config_browsing(conf, win, cwd, EDITING)
                    dirs_and_files = cwd.get_all_items()
                    conf.file_to_open = os.getcwd()+'/'+dirs_and_files[win.cursor.row]
                    conf.right_win.reset_shifts()
                    conf.right_win.set_cursor(conf.right_win.begin_y, conf.right_win.begin_x)
                    return conf
        except PermissionError as err:
            log("browsing | "+str(err))
            pass
        except Exception as err:
            log("browsing | "+str(err))
            return conf


def get_directory_content():
    path = os.getcwd() # current working directory
    files, dirs = [], []
    for (dir_path,dir_names,file_names) in os.walk(path):
        files.extend(file_names)
        dirs.extend(dir_names)
        break
    dirs.sort()
    files.sort()
    return Directory(path, dirs, files)

def show_directory_content(screen, win, cwd, highlight, normal):
    screen.erase()
    screen.border(0)

    shift = win.row_shift
    if shift > 0:
        dirs, files = cwd.get_shifted_dirs_and_files(shift)
    else:
        dirs = cwd.dirs
        files = cwd.files

    try:
        if cwd.is_empty():
            screen.addstr(1, 1, "This directory is empty", normal | curses.A_BOLD)
        else:
            i=1
            for dir_name in dirs:
                if i > win.end_y - 1:
                    break
                coloring = (highlight if i+shift == win.cursor.row+1 else normal)
                screen.addstr(i, 1, str(i+shift) + " - " + dir_name[:win.end_x - 1], coloring | curses.A_BOLD)
                i+=1
            for file_name in files:
                if i > win.end_y - 1:
                    break
                coloring = highlight if i+shift == win.cursor.row+1 else normal
                screen.addstr(i, 1, str(i+shift) + " - " + file_name[:win.end_x - 1], coloring)
                i+=1
    except Exception as err:
        log("show directory | "+str(err))
    finally:
        screen.refresh()




def config_browsing(conf, win, cwd, mode=None):
    conf.left_win = win
    conf.cwd = cwd
    if mode:
        conf.set_mode(mode)
    return conf

def config_editing(conf, win, buffer, mode=None):
    conf.right_win = win
    conf.file_buffer = buffer
    if mode:
        conf.set_mode(mode)
    return conf

EXIT_WITHOUT_SAVING_MESSAGE = """WARNING: Exit without saving.\n\
    Press F2 to save and exit.\n\
    Press ESC again to force exiting without saving.\n\
    Press any other key to continue editing your file."""

def quit_program(stdscr, conf):
    if conf.file_buffer:
        if conf.file_buffer.is_saved:
            return True
        elif conf.file_buffer.original_buff == conf.file_buffer.lines:
            return True
        else:
            print_error_message(conf.right_screen, EXIT_WITHOUT_SAVING_MESSAGE) # warning message
            pressed_key = stdscr.getch()
            if pressed_key == curses.ascii.ESC : # force exit without saving
                return True
            elif pressed_key == curses.KEY_F2: # save and exit
                write_file(conf.file_to_open, conf.file_buffer)
                return True
            else:
                return False
    else:
        return True

""" **************************** EDITING **************************** """

def editing(stdscr, conf):
    curses.curs_set(1) # set cursor as visible
    screen = conf.right_screen
    win = conf.right_win

    """ open and load file """
    if not conf.file_to_open: # there is no file to open and edit
        conf.set_browsing_mode()
        return conf
    if not conf.file_buffer: # file wasnt loaded yet
        buffer = get_file_content(screen, conf.file_to_open)
        if not buffer:
            conf.set_exit_mode()
            return conf
        conf.file_buffer = buffer
    else:
        buffer = conf.file_buffer # file was already loaded


    while True:
        try:
            """ print current content of file """
            show_file_content(screen, win, buffer, conf.highlight, conf.normal)

            """ move cursor """
            new_row, new_col = win.get_cursor_position()
            stdscr.move(new_row, new_col)
        except Exception as err:
            log("editing | "+str(err))
            conf.set_exit_mode()
            return conf

        key = stdscr.getch()
        try:
            if key == ESC: # ESC or curses.ascii.ESC
                conf = config_editing(conf, win, buffer)
                if quit_program(stdscr, conf):
                    conf.set_exit_mode()
                    return conf
                else:
                    show_file_content(screen, win, buffer, conf.highlight, conf.normal)
                    continue
            elif key == ord('\t'): # change focus
                conf = config_editing(conf, win, buffer)
                if quit_program(stdscr, conf):
                    conf.set_browsing_mode()
                    show_file_content(screen, win, buffer, conf.highlight, conf.normal)
                    return conf
                else:
                    show_file_content(screen, win, buffer, conf.highlight, conf.normal)
                    continue
            elif key == curses.KEY_UP:
                win.up(buffer, use_restrictions=True)
            elif key == curses.KEY_DOWN:
                win.down(buffer, use_restrictions=True)
            elif key == curses.KEY_LEFT:
                win.left(buffer)
            elif key == curses.KEY_RIGHT:
                win.right(buffer)
            elif key == curses.KEY_DC: # \x04 for MacOS which doesnt correctly decode delete key
                buffer.delete(win)
            elif key == curses.KEY_BACKSPACE: # \x7f for MacOS
                if (win.cursor.row, win.cursor.col) > (win.begin_y, win.begin_x):
                    win.left(buffer)
                    buffer.delete(win)
            elif key == curses.KEY_F2: # save file
                write_file(conf.file_to_open, buffer)
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen = conf.right_screen
                win = conf.right_win
            elif key == ord('\n'):
                # log(f"NEW LINE - old cursor row {win.cursor.row} col {win.cursor.col}")
                buffer.newline(win)
                win.right(buffer)
                # log(f"NEW LINE - new cursor row {win.cursor.row} col {win.cursor.col}")
            else:
                str_key = chr(key)
                # if str_key[:3] != "KEY":
                if True:
                    buffer.insert(win, str_key)
                    win.right(buffer)
                    # for _ in str_key:
                        # win.right(buffer)
        except Exception as err:
            log("editing | "+str(err))
            return conf


def write_file(file_name, buffer):
    with open(file_name, 'w') as f:
        lines = '\n'.join(buffer.lines)
        f.write(lines)
    buffer.set_save_status(True)


def get_file_content(screen, file_name):
    buffer = None
    try:
        with open(file_name) as f:
            lines = f.read().splitlines()
            buffer = Buffer(file_name, lines)
    except PermissionError as err:
        log("read file | "+str(err))
        print_error_message(screen, "Permission Error")
    except FileNotFoundError as err:
        log("read file | "+str(err))
        print_error_message(screen, "File Not Found Error")
    except Exception as err:
        log("read file | "+str(err))
        print_error_message(screen, str(err))
    finally:
        return buffer

""" print file content but only for max rows and cols of window """
def show_file_content(screen, win, buffer, highlight, normal):
    screen.erase()
    screen.border(0)

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y

    try:
        if buffer:
            for row, line in enumerate(buffer[win.row_shift : max_rows + win.row_shift - 1]):
                if (row + win.begin_y == win.cursor.row - win.row_shift) and (win.col_shift > 0):
                    line = line[win.col_shift + 1:]
                if len(line) > max_cols:
                    line = line[:max_cols - 1]
                screen.addstr(row+1, 1, line, normal)
    except Exception as err:
        log("show file | "+str(err))
    finally:
        screen.refresh()


def print_error_message(screen, message, coloring=None):
    log(str(message))
    screen.erase()
    screen.addstr(1, 1, str(message), coloring if coloring else curses.A_BOLD)
    screen.border(0)
    screen.refresh()


if __name__ == "__main__":
    """ clear log file """
    with open(LOG_FILE, 'w+'):
        pass

    stdscr = curses.initscr()
    stdscr.keypad(True) # enable read special keys
    curses.wrapper(main)
    curses.endwin()
