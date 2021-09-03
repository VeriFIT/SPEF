import curses
import sys
import os


class Buffer(object):
    def __init__(self,win,lines):
        self.win = win
        self.lines = lines
        self.buffer = [""]

    def write(self,text):
        lines = text.split("\n")
        self.buffer[-1] += lines[0]
        self.buffer.extend(lines[1:])
        self.refresh()

    def writeln(self,text):
        self.write(text+"\n")

    def refresh(self):
        self.win.clear()
        for i,line in enumerate(self.buffer[-self.lines:]):
            self.win.addstr(i,0,line)
            self.win.refresh()


"""
scrolling menu for selecting an action
"""
def menu(stdscr):
    curses.curs_set(0) # set cursor as invisible

    """ set coloring """
    curses.start_color()
    curses.init_pair(1,curses.COLOR_BLACK,curses.COLOR_CYAN)
    highlight = curses.color_pair(1)
    normal = curses.A_NORMAL

    """ init list of items for menu """
    items = ["open & read", "open & write", "delete", "rename"]
    number_of_items = len(items)
    max_row = 10 # max number of items


    """ create menu box inside main screen """
    box = curses.newwin(max_row+2,50,1,1)
    box.box()

    current_position = 1 # current selected item
    print_items(stdscr, box, max_row, highlight, normal, current_position, items)

    while True:
        """ get key """
        pressed_key = stdscr.getch()

        # 27 is code for Esc key
        if pressed_key == 27:
            break
        if pressed_key == ord('q'):
            break

        if pressed_key == curses.KEY_DOWN:
            # current position is not on last item
            if current_position < number_of_items:
                current_position = current_position + 1
            else:
                current_position = 1
        if pressed_key == curses.KEY_UP:
            # current position is not on first item
            if current_position > 1:
                current_position = current_position - 1
            else:
                current_position = number_of_items

        """ press enter to print chosen item from menu """
        if pressed_key == ord("\n") and number_of_items != 0:
            stdscr.erase()
            stdscr.border(0)
            stdscr.addstr(14,3,"You choose item '" + items[current_position-1] + "' on position " + str(current_position))

        box.erase()
        box.border(0)
        stdscr.border(0)

        print_items(stdscr, box, max_row, highlight, normal, current_position, items)


def run(stdscr):
    curses.echo()

    lines = curses.LINES
    columns = curses.COLS
    half_width = int(columns/2)

    """ init left and right window """
    left_win = curses.newwin(lines,half_width)
    right_win = curses.newwin(lines,half_width,0,half_width+2)

    left_buffer = Buffer(left_win,lines)
    right_buffer = Buffer(right_win,lines)

    """ set coloring """
    curses.start_color()
    curses.init_pair(1,curses.COLOR_WHITE,curses.COLOR_BLACK)

    left_win.bkgd(' ',curses.color_pair(1))
    right_win.bkgd(' ',curses.color_pair(1))
    stdscr.bkgd(' ',curses.color_pair(1) | curses.A_REVERSE)
    stdscr.refresh()
    right_buffer.refresh()
    left_buffer.refresh()

    """ print something into right window """
    file_name = "mydir/example.txt"
    with open(file_name,'r') as f:
        data = f.read()

    right_buffer.writeln("Test")
    right_buffer.refresh()

    right_buffer.writeln(data)
    right_buffer.refresh()





    stdscr.getch()


if __name__ == "__main__":

    stdscr = curses.initscr()
    stdscr.keypad(True) # enable read special keys

    curses.wrapper(run)

    curses.endwin()

