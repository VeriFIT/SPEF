
import curses


COL_BKGD = 1
COL_SELECT = 2
COL_BORDER = 3
COL_HELP = 4

COL_FILTER = 10
COL_TITLE = 11

COL_NOTE = 30
COL_NOTE_LIGHT = 31
COL_LINE_NUM = 32


# highlight colors for syntax (40-60)
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
HL_DARK_BLUE = 55


# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses

def init_color_pairs():
    curses.init_pair(COL_BKGD, curses.COLOR_WHITE, -1)
    curses.init_pair(COL_SELECT, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(COL_BORDER, curses.COLOR_CYAN, -1)
    curses.init_pair(COL_HELP, 166, -1)
    curses.init_pair(COL_FILTER, 9, -1)
    curses.init_pair(COL_TITLE, curses.COLOR_GREEN, -1)

    curses.init_pair(COL_NOTE, curses.COLOR_BLACK, 11)
    curses.init_pair(COL_NOTE_LIGHT, curses.COLOR_BLACK, 221)
    curses.init_pair(COL_LINE_NUM, 12, -1)


    """ syntax highlight colors """
    curses.init_pair(HL_PURPLE, 171, -1)
    curses.init_pair(HL_BLUE, 39, -1)
    curses.init_pair(HL_LIGHT_BLUE, 117, -1)
    curses.init_pair(HL_YELLOW, 229, -1)

    curses.init_pair(HL_CYAN, 43, -1)
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
    curses.init_pair(HL_DARK_BLUE, 27, -1)

