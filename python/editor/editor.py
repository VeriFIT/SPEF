import argparse
import curses

from cursor import Cursor
from window import Window
from buffer import Buffer


def up(win, buffer, cursor):
    cursor.up(buffer)
    win.up(cursor)
    win.horizontal_shift(cursor)

def down(win, buffer, cursor):
    cursor.down(buffer)
    win.down(buffer,cursor)
    win.horizontal_shift(cursor)

def left(win, buffer, cursor):
    cursor.left(buffer)
    win.up(cursor)
    win.horizontal_shift(cursor)

def right(win, buffer, cursor):
    cursor.right(buffer)
    win.down(buffer,cursor)
    win.horizontal_shift(cursor)

def main(stdscr):
    """ parsing arguments """
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    """ read file from argument """
    with open(args.filename) as f:
        lines = f.read().splitlines()
        buffer = Buffer(lines)
        # buffer = f.readlines()


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
        new_row, new_col = win.get_shifted_cursor_position(cursor)
        stdscr.move(new_row,new_col)
        # stdscr.move(*win.get_shifted_cursor_position(cursor))

        key = stdscr.getkey()

        if key == "q": # press ESC to exit
            break
        elif key == "KEY_UP":
            up(win,buffer, cursor)
        elif key == "KEY_DOWN":
            down(win,buffer, cursor)
        elif key == "KEY_LEFT":
            left(win,buffer, cursor)
        elif key == "KEY_RIGHT":
            right(win,buffer, cursor)
        elif key == "\n":
            buffer.split(cursor)
            right(win, buffer, cursor)
        elif key in ("KEY_DC","\x04"): # \x04 for MacOS which doesnt correctly decode delete key
            buffer.delete(cursor)
        elif key in ("KEY_BACKSPACE","\x7f"): # \x7f for MacOS
            if (cursor.row, cursor.col) > (0,0):
                left(win, buffer, cursor)
                buffer.delete(cursor)
        else:
            str_key = str(key)
            if str_key[:3] != "KEY":
                buffer.insert(cursor, key)
                for _ in key:
                    right(win, buffer, cursor)



if __name__=="__main__":
    stdscr = curses.initscr()
    curses.wrapper(main)
    curses.endwin()
