import argparse
import curses
import curses.ascii

from cursor import Cursor
from window import Window
from buffer import Buffer

ESC = 27

"""
********** TODO **********
-dynamic reading of file
-line numbering
-change focus between windows using TAB
-display name of opened file (at a status line at the bottom of the window)
-hint line with key shortcuts
-show help (ctrl+h)
-add comment (with line number) into extern report (and create extern report for file)
-add tag to file
-syntax highlight - token parser for languages
-key shortcut for save and exit
-key shortcut for forced exit without saving

***************************


********** DONE **********
-read file
-save file (ctrl+w)
-backspace, delete
-insert

**************************
"""

def read_file(filename):
    with open(filename) as f:
        lines = f.read().splitlines()
        buffer = Buffer(lines)
    return buffer


def write_file(filename, buffer):
    with open(filename, 'w') as f:
        lines = '\n'.join(buffer.lines)
        f.write(lines)
    buffer.set_save_status(True)


def main(stdscr):
    curses.set_tabsize(4)
    curses.set_escdelay(1)

    """ parsing arguments """
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    """ read file from argument """
    filename = args.filename
    buffer = read_file(filename)

    win = Window(curses.LINES - 1, curses.COLS - 1)
    cursor = Cursor()


    while True:
        stdscr.erase()

        """ print file content but only for max rows and cols of window """
        for row,line in enumerate(buffer[win.row_shift : win.max_rows + win.row_shift]):
            if (row == cursor.row - win.row_shift) and (win.col_shift > 0):
                line = line[win.col_shift + 1:]
            if len(line) > win.max_cols:
                line = line[:win.max_cols - 1]
            stdscr.addstr(row, 0, line)

        """ move cursor """
        new_row, new_col = win.get_shifted_cursor_position(cursor.row, cursor.col)
        stdscr.move(new_row,new_col)


        key = stdscr.getkey()


        if key == "\x1B" : # press ESC to exit
            if buffer.is_saved:
                break
            else:
                if buffer.original_buff == buffer.lines:
                    break
                # TODO: warning for unsaved changes
                warning_key = stdscr.getkey()
                if curses.ascii.iscntrl(key):
                    warning_ctrl_key = curses.ascii.unctrl(warning_key)
                    # press ctrl+f to force exit
                    if warning_ctrl_key == "^F":
                        break
                    # press ctrl+q to save and exit
                    if warning_ctrl_key == "^W":
                        write_file(filename, buffer)
                        break
                # press other key for cancel exiting
                else:
                    continue
        elif key == "\n":
            buffer.newline(cursor)
            right(win, buffer, cursor)
        elif key == "\t":
            # buffer.tab(cursor)
            pass
        elif key == "KEY_RESIZE":
            # window resize
            pass
        # ARROWS
        elif key == "KEY_UP":
            up(win, buffer, cursor)
        elif key == "KEY_DOWN":
            down(win, buffer, cursor)
        elif key == "KEY_LEFT":
            left(win, buffer, cursor)
        elif key == "KEY_RIGHT":
            right(win, buffer, cursor)
        elif key in ("KEY_DC","\x04"): # \x04 for MacOS which doesnt correctly decode delete key
            buffer.delete(cursor)
        elif key in ("KEY_BACKSPACE","\x7f"): # \x7f for MacOS
            if (cursor.row, cursor.col) > (0,0):
                left(win, buffer, cursor)
                buffer.delete(cursor)
        # CTRL KEYS
        elif curses.ascii.iscntrl(key):
            ctrl_key = curses.ascii.unctrl(key)
            if ctrl_key == '^W': # press ctrl+w to write buffer into file
                write_file(filename, buffer)
        else:
            str_key = str(key)
            if str_key[:3] != "KEY":
                buffer.insert(cursor, key)
                for _ in key:
                    right(win, buffer, cursor)


def up(win, buffer, cursor):
    cursor.up(buffer)
    win.up(cursor.row)
    win.horizontal_shift(cursor.col)

def down(win, buffer, cursor):
    cursor.down(buffer)
    win.down(buffer,cursor.row)
    win.horizontal_shift(cursor.col)

def left(win, buffer, cursor):
    cursor.left(buffer)
    win.up(cursor.row)
    win.horizontal_shift(cursor.col)

def right(win, buffer, cursor):
    cursor.right(buffer)
    win.down(buffer,cursor.row)
    win.horizontal_shift(cursor.col)

def tab_right(win, buffer, cursor):
    cursor.right(buffer)
    while cursor.col % 4 != 0:
        cursor.right(buffer)
        win.horizontal_shift(cursor.col)


if __name__=="__main__":
    stdscr = curses.initscr()
    stdscr.keypad(True) # enable read special keys

    curses.wrapper(main)
    curses.endwin()
