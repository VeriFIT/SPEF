
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

GREEN_COL = 33

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
HL_DARK_GRAY = 50
HL_GRAY = 51
HL_OLIVE = 52
HL_PINK = 53
HL_DARK_YELLOW = 54


# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses

def init_color_pairs():
    curses.init_pair(BKGD, curses.COLOR_WHITE, -1)
    curses.init_pair(SELECT, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(BORDER, curses.COLOR_CYAN, -1)
    curses.init_pair(HELP, 166, -1)
    # curses.init_pair(HELP_ACTION, 7, -1)
    curses.init_pair(FILTER, 9, -1)

    curses.init_pair(TAG_MGMT, 10, -1)

    curses.init_pair(NOTE_HIGHLIGHT, curses.COLOR_BLACK, 11)
    # curses.init_pair(NOTE_HIGHLIGHT, curses.COLOR_BLACK, 59)
    curses.init_pair(NOTE_MGMT, curses.COLOR_BLACK, 221)
    # curses.init_pair(NOTE_MGMT, 11, -1)
    curses.init_pair(LINE_NUM, 12, -1)

    curses.init_pair(GREEN_COL, curses.COLOR_GREEN, -1)

    """ syntax highlight colors """
    # curses.init_pair(HL_PURPLE, 133, -1)
    curses.init_pair(HL_PURPLE, 171, -1)
    # curses.init_pair(HL_BLUE, 75, -1)
    # curses.init_pair(HL_BLUE, 27, -1)
    curses.init_pair(HL_BLUE, 39, -1)
    curses.init_pair(HL_LIGHT_BLUE, 117, -1)
    curses.init_pair(HL_YELLOW, 229, -1)

    # curses.init_pair(HL_CYAN, 36, -1)
    curses.init_pair(HL_CYAN, 43, -1)
    # curses.init_pair(HL_GREEN, 22, -1)
    curses.init_pair(HL_GREEN, 71, -1)
    curses.init_pair(HL_PASTEL_GREEN, 151, -1)
    curses.init_pair(HL_ORANGE, 209, -1)
    curses.init_pair(HL_RED, 160, -1)

    curses.init_pair(HL_LIGHT_GRAY, 15, -1)
    curses.init_pair(HL_DARK_GRAY, 8, -1)
    curses.init_pair(HL_GRAY, 7, -1)
    curses.init_pair(HL_OLIVE, 94, -1)

    curses.init_pair(HL_PINK, 219, -1)
    curses.init_pair(HL_DARK_YELLOW, 11, -1)

