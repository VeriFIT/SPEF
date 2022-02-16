
import curses


# TODO: pridat vsade COLOR_XXX !!!

BKGD = 1
SELECT = 2
BORDER = 3
HELP = 4
# HELP_KEY = 5
# HELP_ACTION = 6

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
    curses.init_pair(BORDER, curses.COLOR_CYAN, -1)
    curses.init_pair(HELP, 166, -1)
    # curses.init_pair(HELP, 161, -1)
    # curses.init_pair(HELP_ACTION, 7, -1)
    curses.init_pair(FILTER, 9, -1)

    curses.init_pair(TAG_MGMT, 10, -1)

    curses.init_pair(NOTE_HIGHLIGHT, curses.COLOR_BLACK, 11)
    curses.init_pair(NOTE_MGMT, curses.COLOR_BLACK, 221)
    # curses.init_pair(NOTE_MGMT, 11, -1)
    curses.init_pair(LINE_NUM, 12, -1)

    # curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
