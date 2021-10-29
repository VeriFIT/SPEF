
import curses
import curses.ascii
import os
import sys


from buffer import Buffer
from config import Config
from cursor import Cursor
from directory import Directory
from window import Window


ESC = 27 # Esc key code is 27


def clear_all(stdscr,left_screen,right_screen):
    stdscr.erase()
    left_screen.erase()
    right_screen.erase()

    stdscr.border(0)
    left_screen.border(0)
    right_screen.border(0)
    
    stdscr.refresh()
    left_screen.refresh()
    right_screen.refresh()


"""
browsing in the directory structure
"""
def main(stdscr):
    stdscr.clear()

    curses.set_escdelay(1)

    """ create win for browsing files and win for editing files """
    win_heigh = curses.LINES - 2
    win_width = int(curses.COLS / 2)
    
    left_screen = curses.newwin(win_heigh, win_width, 1, 1) # for browsing (1,1) ... (h,w)
    right_screen = curses.newwin(win_heigh, win_width-1, 1, win_width+1) # for editing (1,w) ... (h,ww)

    """ set coloring """
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

    highlight = curses.color_pair(1)
    normal = curses.A_NORMAL
    
    stdscr.bkgd(' ', curses.color_pair(2))
    left_screen.bkgd(' ', curses.color_pair(2))
    right_screen.bkgd(' ', curses.color_pair(2))

    clear_all(stdscr,left_screen,right_screen)


    """ create config """
    config = Config(left_screen, right_screen)
    config.set_coloring(highlight, normal)

    config.left_win = Window(win_heigh, win_width, 0, 0)
    config.right_win = Window(win_heigh, win_width-1, 2, win_width+2)


    """ get current files and dirs """
    cwd = get_directory_content()
    config.set_current_directory(cwd)
    
    config.left_cursor = Cursor()
    config.right_cursor = Cursor()


    while True:
        """ browsing """
        config, brows_res = browsing(stdscr, config)
        if brows_res == 0: # ESC
            break
        elif brows_res == 1: # change focus to edit win
            """ editing """
            config, edit_res = editing(stdscr, config)
            if edit_res == 0: # ESC
                break
            elif edit_res == 1: # change focus to brows win
                continue


""" **************************** BROWSING **************************** """

def browsing(stdscr, conf):
    curses.curs_set(0) # set cursor as invisible

    screen = conf.left_screen
    win = conf.left_win
    cursor = conf.left_cursor # used more like a position
    cwd = conf.brows_dir

    while True:
        """ print current directory structure """
        show_directory_content(screen, win, cursor, cwd, conf.highlight, conf.normal)

        key = stdscr.getkey()
        try:
            if key == "\x1B" : # ESC
                conf = config_browsing(conf, win, cursor, cwd) # save browsing state before exit browsing
                return conf, 0
            elif key == "\t": # change focus
                conf = config_browsing(conf, win, cursor, cwd)
                return conf, 1
            elif key == "KEY_UP":
                cursor.up(cwd, win, use_restrictions=False)
                win.up(cursor.row)
            elif key == "KEY_DOWN":
                cursor.down(cwd, win, use_restrictions=False)
                win.down(cwd, cursor.row)
            elif key == "KEY_RIGHT":
                # if cursor.row <= len(cwd.dirs): # without borders
                if cursor.row < len(cwd.dirs): # with borders
                    """ change current directory to subdirectory """
                    # os.chdir(os.getcwd()+'/'+cwd.dirs[cursor.row-1]) # without borders
                    os.chdir(os.getcwd()+'/'+cwd.dirs[cursor.row]) # with borders
                    cwd = get_directory_content()
                    win.reset_shifts()
                    cursor.row = 0 # set cursor on first position (first item)
                else:
                    """ view file """
                    pass
            elif key == "KEY_LEFT":
                """ change current directory to parent directory """
                current_dir = os.path.basename(os.getcwd()) # get directory name
                if current_dir: # if its not root
                    os.chdir('..')
                    cwd = get_directory_content()
                    win.reset_shifts()
                    cursor.row = 0

                    dir_position = cwd.dirs.index(current_dir) # find position of prev directory
                    if dir_position:
                        for i in range(0, dir_position): # set cursor position to prev directory
                            cursor.down(cwd, win, use_restrictions=False)
                            win.down(cwd, cursor.row)
            elif key == "v": # F3
                """ view file """
                pass
            elif key == "o": # F4
                """ open file to edit and change focus """
                if cursor.row >= len(cwd.dirs):
                    conf = config_browsing(conf, win, cursor, cwd)
                    dirs_and_files = cwd.get_all_items()
                    conf.file_to_open = os.getcwd()+'/'+dirs_and_files[cursor.row]
                    return conf, 1
        except Exception as err:
            print_error_message(screen, str(err))
            return conf, -1
        


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

def show_directory_content(screen, win, cursor, cwd, highlight, normal):
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
            screen.addstr(1, 1, "This directory is empty", highlight | curses.A_BOLD)
        else:
            # i=0 # without borders
            i=1 # with borders
            for dir_name in dirs:
                # if i > win.end_row: # without borders
                if i > win.end_row - 2: # with borders
                    break
                # coloring = (highlight if i+shift == cursor.row else normal) # without borders
                coloring = (highlight if i+shift == cursor.row+1 else normal) # with borders
                screen.addstr(i, 1, str(i+shift) + " - " + dir_name[:win.end_col - 1], coloring | curses.A_BOLD)
                i+=1
            for file_name in files:
                # if i > win.end_row: # without borders
                if i > win.end_row - 2: # with borders
                    break
                # coloring = highlight if i+shift == cursor.row else normal # without borders
                coloring = highlight if i+shift == cursor.row+1 else normal # with borders
                screen.addstr(i, 1, str(i+shift) + " - " + file_name[:win.end_col - 1], coloring) # with borders
                i+=1
    except curses.error:
        pass
    finally:
        screen.refresh()


def config_browsing(conf, win, cursor, cwd):
    conf.left_win = win
    conf.left_cursor = cursor
    conf.brows_dir = cwd
    return conf

def config_editing(conf, win, cursor, buffer):
    conf.right_win = win
    conf.right_cursor = cursor
    # conf.file_buffer = buffer
    return conf


""" **************************** EDITING **************************** """

def editing(stdscr, conf):
    curses.curs_set(1) # set cursor as visible

    screen = conf.right_screen
    win = conf.right_win
    cursor = conf.right_cursor

    buffer = get_file_content(screen, conf.file_to_open)
    if not buffer:
        return conf, -1


    while True:
        """ print current content of file """
        show_file_content(screen, win, cursor, buffer, conf.highlight, conf.normal)

        """ move cursor """
        new_row, new_col = win.get_shifted_cursor_position(cursor.row, cursor.col)
        screen.move(new_row,new_col)

        key = stdscr.getkey()
        try:
            if key == "\x1B" : # ESC
                conf = config_editing(conf, win, cursor, buffer) # save browsing state before exit browsing
                return conf, 0
            elif key == "\t": # change focus
                conf = config_editing(conf, win, cursor, buffer) # save browsing state before exit browsing
                return conf, 1
            elif key == "KEY_UP":
                cursor.up(buffer, win, use_restrictions=False)
                win.up(cursor.row)
                # up(win, buffer, cursor)
            elif key == "KEY_DOWN":
                cursor.down(buffer, win, use_restrictions=False)
                win.down(buffer, cursor.row)
                # down(win, buffer, cursor)
            elif key == "KEY_LEFT":
                left(win, buffer, cursor)
            elif key == "KEY_RIGHT":
                right(win, buffer, cursor)
            elif key == "r":
                conf.read_file()
            elif key == "s": # F2
                """ save file """
                pass
        except Exception as err:
            print_error_message(screen, str(err))
            return conf, -1



def get_file_content(screen, file_name):
    buffer = None
    try:
        with open(file_name) as f:
            lines = f.read().splitlines()
            buffer = Buffer(file_name, lines)
    except PermissionError:
        print_error_message(screen, "Permission Error")
    except FileNotFoundError:
        print_error_message(screen, "File Not Found Error")
    except Exception as err:
        print_error_message(screen, str(err))
    finally:
        return buffer


""" print file content but only for max rows and cols of window """
def show_file_content(screen, win, cursor, buffer, highlight, normal):
    screen.erase()
    screen.border(0)

    # borders = 0 # without borders
    borders = 2 # with borders

    try:
        for row, line in enumerate(buffer[win.row_shift : win.end_row - borders + win.row_shift]):
            if (row == cursor.row - win.row_shift) and (win.col_shift > 0):
                line = line[win.col_shift + 1:]
            if len(line) > win.end_col - borders:
                line = line[:win.end_col - 1 - borders]
            # screen.addstr(row, 0, line, normal) # without borders
            screen.addstr(row+1, 1, line, normal) # with borders
        """
        for row, line in enumerate(buffer[win.row_shift : win.max_rows - borders + win.row_shift]):
            if (row == cursor.row - win.row_shift) and (win.col_shift > 0):
                line = line[win.col_shift + 1:]
            if len(line) > win.max_cols - borders:
                line = line[:win.max_cols - 1 - borders]
            # screen.addstr(row, 0, line, normal) # without borders
            screen.addstr(row+1, 1, line, normal) # with borders
        """
    except:
        pass
    finally:
        screen.refresh()


def up(win, buffer, cursor):
    cursor.up(buffer, win)
    win.up(cursor.row)
    # win.horizontal_shift(cursor)

def down(win, buffer, cursor):
    cursor.down(buffer, win)
    win.down(buffer,cursor.row)
    # win.horizontal_shift(cursor)

def left(win, buffer, cursor):
    cursor.left(buffer, win)
    win.up(cursor.row)
    # win.horizontal_shift(cursor)

def right(win, buffer, cursor):
    cursor.right(buffer, win)
    win.down(buffer,cursor.row)
    # win.horizontal_shift(cursor)


def print_error_message(screen, message, coloring=None):
    screen.erase()
    screen.border(0)
    screen.addstr(1, 1, str(message), coloring if coloring else curses.A_BOLD)
    screen.refresh()


if __name__ == "__main__":
    stdscr = curses.initscr()
    stdscr.keypad(True) # enable read special keys
    curses.wrapper(main)
    curses.endwin()
