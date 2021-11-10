import curses

BKGD = 1
SELECT = 2

# filters 
FILTER = 10
EMPTY_FILTER = 11

# tags
TAG_MGMT = 20

# notes
NOTE_MGMT = 30
NOTE_HIGHLIGHT = 31
LINE_NUM = 32

def init_color_pairs():
    curses.init_pair(BKGD, curses.COLOR_WHITE, -1)
    curses.init_pair(SELECT, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(FILTER, 9, -1)

    curses.init_pair(TAG_MGMT, 10, -1)

    curses.init_pair(NOTE_MGMT, 11, -1)
    curses.init_pair(NOTE_HIGHLIGHT, curses.COLOR_BLACK, 11)
    curses.init_pair(LINE_NUM, 12, -1)

    # curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
