
import curses
import curses.ascii
import os
import sys


from buffer import Buffer
from config import *
from directory import Directory
from window import Window, Cursor


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

    config.right_win = Window(win_heigh, win_width-1, 2, win_width+2)
    config.left_win = Window(win_heigh, win_width, 0, 1)
    config.left_win.set_cursor(0,0)


    """ get current files and dirs """
    config.cwd = get_directory_content()

    while True:
        if config.mode == EXIT:
            stdscr.getkey()
            break
        elif config.mode == BROWSING:
            config = browsing(stdscr, config)
        elif config.mode == EDITING:
            config = editing(stdscr, config)
            # break


""" **************************** BROWSING **************************** """

def browsing(stdscr, conf):
    curses.curs_set(0) # set cursor as invisible

    screen = conf.left_screen
    win = conf.left_win
    cwd = conf.cwd

    while True:
        """ print current directory structure """
        show_directory_content(screen, win, cwd, conf.highlight, conf.normal)

        key = stdscr.getkey()
        try:
            if key == "\x1B" : # ESC
                conf = config_browsing(conf, win, cwd) # save browsing state before exit browsing
                conf.set_exit_mode()
                return conf
            elif key == "\t": # change focus
                conf = config_browsing(conf, win, cwd)
                conf.set_editing_mode()
                return conf
            elif key == "KEY_UP":
                win.up(cwd, use_restrictions=False)
            elif key == "KEY_DOWN":
                win.down(cwd, use_restrictions=False)
            elif key == "KEY_RIGHT":
                if win.cursor.row < len(cwd.dirs):
                    """ change current directory to subdirectory """
                    os.chdir(os.getcwd()+'/'+cwd.dirs[win.cursor.row])
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0) # set cursor on first position (first item)
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
                    win.set_cursor(0,0)

                    dir_position = cwd.dirs.index(current_dir) # find position of prev directory
                    if dir_position:
                        for i in range(0, dir_position): # set cursor position to prev directory
                            win.down(cwd, use_restrictions=False)
            elif key == "v": # F3
                """ view file """
                pass
            elif key == "o": # F4
                """ open file to edit and change focus """
                if win.cursor.row >= len(cwd.dirs):
                    conf = config_browsing(conf, win, cwd)
                    dirs_and_files = cwd.get_all_items()
                    conf.file_to_open = os.getcwd()+'/'+dirs_and_files[win.cursor.row]
                    conf.right_win.reset_shifts()
                    conf.right_win.set_cursor(conf.right_win.begin_y, conf.right_win.begin_x)
                    conf.set_editing_mode()
                    return conf
        except PermissionError:
            pass
        except Exception as err:
            print_error_message(screen, str(err))
            conf.set_exit_mode()
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
    except curses.error:
        pass
    finally:
        screen.refresh()


def config_browsing(conf, win, cwd):
    conf.left_win = win
    conf.cwd = cwd
    return conf

def config_editing(conf, win, buffer):
    conf.right_win = win
    conf.file_buffer = buffer
    return conf


""" **************************** EDITING **************************** """

def editing(stdscr, conf):
    curses.curs_set(1) # set cursor as visible

    screen = conf.right_screen
    win = conf.right_win

    buffer = get_file_content(screen, conf.file_to_open)
    if not buffer:
        conf.set_exit_mode()
        return conf


    while True:
        """ print current content of file """
        show_file_content(screen, win, buffer, conf.highlight, conf.normal)
        """
        screen.erase()
        screen.border(0)
        new_row, new_col = win.get_cursor_position()
        screen.addstr(1, 1, "cursor: "+str(win.cursor.row)+", "+str(win.cursor.col)+" - "+str(new_row)+", "+str(new_col), conf.normal) # with borders
        screen.addstr(2, 1, "shift:  "+str(win.row_shift)+", "+str(win.col_shift), conf.normal) # with borders
        screen.addstr(3, 1, "begin:  "+str(win.begin_y)+", "+str(win.begin_x), conf.normal) # with borders
        screen.addstr(4, 1, "end:    "+str(win.end_y)+", "+str(win.end_x), conf.normal) # with borders
        screen.addstr(5, 1, "bottom: "+str(win.bottom), conf.normal) # with borders
        screen.addstr(6, 1, "buffer: "+str(len(buffer)), conf.normal) # with borders
        screen.refresh()
        """

        """ move cursor """
        new_row, new_col = win.get_cursor_position()
        stdscr.move(new_row, new_col)

        key = stdscr.getkey()
        try:
            if key == "\x1B" : # ESC
                conf = config_editing(conf, win, buffer) # save browsing state before exit browsing
                conf.set_exit_mode()
                return conf
            elif key == "\t": # change focus
                conf = config_editing(conf, win, buffer) # save browsing state before exit browsing
                conf.set_browsing_mode()
                return conf
            elif key == "KEY_UP":
                win.up(buffer, use_restrictions=True)
                win.horizontal_shift()
            elif key == "KEY_DOWN":
                win.down(buffer, use_restrictions=True)
                win.horizontal_shift()
            elif key == "KEY_LEFT":
                win.left(buffer)
                win.horizontal_shift()
            elif key == "KEY_RIGHT":
                win.right(buffer)
                win.horizontal_shift()
            elif key in ("KEY_DC","\x04"): # \x04 for MacOS which doesnt correctly decode delete key
                buffer.delete(win)
            elif key in ("KEY_BACKSPACE","\x7f"): # \x7f for MacOS
                if (win.cursor.row, win.cursor.col) > (win.begin_y, win.begin_x):
                    win.left(buffer)
                    buffer.delete(win)
            elif key == "r":
                pass
            elif key == "s": # F2
                """ save file """
                pass
        except Exception as err:
            print_error_message(screen, str(err))
            conf.set_exit_mode()
            return conf



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
def show_file_content(screen, win, buffer, highlight, normal):
    screen.erase()
    screen.border(0)

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y

    try:
        for row, line in enumerate(buffer[win.row_shift : max_rows + win.row_shift - 1]):
            if (row + win.begin_y == win.cursor.row - win.row_shift) and (win.col_shift > 0):
                line = line[win.col_shift + 1:]
            if len(line) > max_cols:
                line = line[:max_cols - 1]
            screen.addstr(row+1, 1, line, normal)
    except:
        pass
    finally:
        screen.refresh()


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
