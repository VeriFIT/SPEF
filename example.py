import curses

def init_win():
    stdscr = curses.initscr()
    curses.noecho() # reading input without displaying it
    stdscr.keypad(True) # enable read special keys
    return stdscr



def main(stdscr):
    stdscr.clear()

    for i in range(0,11):
        v=i-10
        stdscr.addstr(i,0,'10 plus {} is {}'.format(v,10+v))
    stdscr.refresh()
    stdscr.getkey()


def foo(number,win):
    win.addstr(1,1,'{}'.format(number))
    win.refresh()
    win.getkey()

if __name__ == "__main__":

    stdscr = init_win()

    curses.wrapper(main)
    # foo(2,stdscr)
    # curses.wrapper(foo,2,stdscr)

    curses.endwin()
