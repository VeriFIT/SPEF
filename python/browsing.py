import curses
import sys
import os

from directory import Content


ESC = 27 # Esc key code is 27



"""
create main window
"""
def init_win():
    stdscr = curses.initscr()
    curses.noecho() # reading input without displaying it
    stdscr.keypad(True) # enable read special keys
    return stdscr


""" 
function returns list of directories and list of files at given path
"""
def get_dirs_and_files():
    path = os.getcwd() # current working directory
    files, dirs = [], []
    for (dirpath,dirnames,filenames) in os.walk(path):
        files.extend(filenames)
        dirs.extend(dirnames)
        break
    dirs.sort()
    files.sort()
    return Content(path, dirs, files)


def print_dirs_and_files(stdscr, box, end, highlight, normal, cwd):
    stdscr.erase()
    box.erase()
    box.border(0)

    if cwd.shift > 0:
        dirs, files = cwd.get_shifted_dirs_and_files()
    else:
        dirs = cwd.dirs
        files = cwd.files
    try:
        if cwd.is_empty():
            box.addstr(1, 2, "This directory is empty", highlight | curses.A_BOLD)
        else:
            i=1
            for dir_name in dirs:
                if i <= end:
                    box.addstr(i, 2, str(i+cwd.shift) + " - " + dir_name, (highlight if i+cwd.shift == cwd.position else normal) | curses.A_BOLD)
                    i+=1
            for file_name in files:
                if i <= end:
                    box.addstr(i, 2, str(i+cwd.shift) + " - " + file_name, highlight if i+cwd.shift == cwd.position else normal)
                    i+=1
    except curses.error:
        pass

    stdscr.refresh()
    box.refresh()


"""
browsing in the directory structure
"""
def browsing(stdscr):
    stdscr.erase()
    stdscr.border(0)
    stdscr.refresh()
    curses.curs_set(0) # set cursor as invisible

    """ create menu box inside main screen """
    box_heigh = curses.LINES - 2
    box_width = int (curses.COLS / 2)
    box_rows = box_heigh - 2
    box = curses.newwin(box_heigh,box_width,1,1)
    # box.box()
    # box.box("|","-")


    """ set coloring """
    curses.start_color()
    curses.init_pair(1,curses.COLOR_BLACK,curses.COLOR_CYAN)
    curses.init_pair(2,curses.COLOR_WHITE,curses.COLOR_BLACK)

    stdscr.bkgd(' ',curses.color_pair(2))
    box.bkgd(' ',curses.color_pair(2))

    highlight = curses.color_pair(1)
    normal = curses.A_NORMAL


    """ init list of items for menu """
    cwd = get_dirs_and_files()
    cursor = 1 # first item

    print_dirs_and_files(stdscr, box, box_rows, highlight, normal, cwd)

    while True:
        """ get key """
        pressed_key = stdscr.getch()

        if pressed_key == ESC:
            break
        if pressed_key == ord('q'): # quit
            break

        if pressed_key == ord('f'): # find
            pass

        if pressed_key == ord('m'): # menu
            pass

        """ KEY DOWN """
        if pressed_key == curses.KEY_DOWN:
            if (cursor == box_rows) and (cwd.position < cwd.item_count): # current position is on last row but not on last item on menu
                cwd.up_shift() # move all items up
            if cursor < box_rows:
                cursor += 1
            cwd.go_down()
        """ KEY UP """
        if pressed_key == curses.KEY_UP:
            if (cursor == 1) and (cwd.position > 1): # current position is on first row but not on first item on menu
                cwd.down_shift() # move all items down
            if cursor > 1:
                cursor -= 1
            cwd.go_up()

        try:
            """ KEY LEFT """
            if pressed_key == curses.KEY_LEFT:
                os.chdir('..') # go out of directory
                cwd = get_dirs_and_files()
                cursor = 1
            """ KEY RIGHT """
            if pressed_key == curses.KEY_RIGHT:
                if cwd.position <= len(cwd.dirs):
                    os.chdir(os.getcwd()+'/'+cwd.dirs[cwd.position-1]) # go into chosen directory
                    cwd = get_dirs_and_files()
                    cursor = 1
        except PermissionError:
            pass
        except NotADirectoryError:
            pass
        except FileNotFoundError:
            pass

        """ press enter to print chosen item from menu """
        """
        if pressed_key == ord("\n") and number_of_items != 0:
            stdscr.erase()
            stdscr.border(0)
            stdscr.addstr(14,3,"You choose item " + str(current_item))
        """

        print_dirs_and_files(stdscr, box, box_rows, highlight, normal, cwd)


if __name__ == "__main__":

    stdscr = init_win()

    """ 
    # wrapper takes function name and its arguments (without first implicit argument stdscr (main window))
    wrapper example usage:
        curses.wrapper(function, arg1, arg2)
        def function(stdscr, arg1, arg2)
    """

    curses.wrapper(browsing)


    curses.endwin()
