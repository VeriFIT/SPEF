
import curses


# TODO: pridat vsade COLOR_XXX !!!

BKGD = 1
SELECT = 2
BORDER = 3
HELP = 4
# HELP_KEY = 5
# HELP_ACTION = 6
GREEN_COL = 7

# filters 
FILTER = 10
EMPTY_FILTER = 11

# tags
TAG_MGMT = 20

# notes
NOTE_MGMT = 30
NOTE_HIGHLIGHT = 31
LINE_NUM = 32

# highlight colors (40-60)
HL_PURPLE = 40
HL_BLUE = 41
HL_LIGHT_BLUE = 42
HL_YELLOW = 43
HL_CYAN = 44
HL_GREEN = 45
HL_PASTEL_GREEN = 46
HL_ORANGE = 47
HL_RED = 48
HL_LIGHT_GRAY = 49
HL_GRAY = 50



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
    curses.init_pair(GREEN_COL, curses.COLOR_GREEN, -1)

    curses.init_pair(HL_PURPLE, 171, -1)
    curses.init_pair(HL_BLUE, 39, -1) # 27
    curses.init_pair(HL_LIGHT_BLUE, 117, -1)
    curses.init_pair(HL_YELLOW, 229, -1)

    curses.init_pair(HL_CYAN, 49, -1)
    curses.init_pair(HL_GREEN, 22, -1) # 34 or 28
    curses.init_pair(HL_PASTEL_GREEN, 193, -1)
    curses.init_pair(HL_ORANGE, 209, -1)
    curses.init_pair(HL_RED, 160, -1)

    curses.init_pair(HL_LIGHT_GRAY, 15, -1)
    curses.init_pair(HL_GRAY, 7, -1)


