import curses


COL_BKGD = 1
COL_SELECT = 2
COL_BORDER = 3
COL_HELP = 4
COL_FILTER = 5
COL_LINE_NUM = 6
COL_NOTE = 7
COL_NOTE_LIGHT = 8


COL_RED = 20
COL_GREEN = 21
COL_BLUE = 22
COL_CYAN = 23
COL_YELLOW = 24
COL_ORANGE = 25
COL_PINK = 26
COL_DARK_BLUE = 27


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
HL_OLIVE = 49
HL_PINK = 50

HL_NORMAL = 55


# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses


def init_color_pairs():
    curses.init_pair(COL_BKGD, -1, -1)
    curses.init_pair(COL_SELECT, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(COL_BORDER, curses.COLOR_CYAN, -1)
    curses.init_pair(COL_HELP, 209, -1)  # 166

    curses.init_pair(COL_FILTER, 160, -1)
    curses.init_pair(COL_LINE_NUM, 12, -1)
    curses.init_pair(COL_NOTE, curses.COLOR_BLACK, 11)
    curses.init_pair(COL_NOTE_LIGHT, curses.COLOR_BLACK, 221)

    curses.init_pair(COL_RED, 160, -1)
    curses.init_pair(COL_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(COL_BLUE, 27, -1)
    curses.init_pair(COL_CYAN, 43, -1)
    curses.init_pair(COL_YELLOW, 11, -1)
    curses.init_pair(COL_ORANGE, 209, -1)
    curses.init_pair(COL_PINK, 219, -1)
    curses.init_pair(COL_DARK_BLUE, curses.COLOR_BLUE, -1)

    """ syntax highlight colors """
    curses.init_pair(HL_PURPLE, 171, -1)
    curses.init_pair(HL_BLUE, 39, -1)
    curses.init_pair(HL_LIGHT_BLUE, 117, -1)
    curses.init_pair(HL_YELLOW, 222, -1)  # 11
    curses.init_pair(HL_CYAN, 43, -1)
    curses.init_pair(HL_GREEN, 71, -1)  # 71
    curses.init_pair(HL_PASTEL_GREEN, 151, -1)
    curses.init_pair(HL_ORANGE, 209, -1)
    curses.init_pair(HL_RED, 160, -1)
    curses.init_pair(HL_OLIVE, 94, -1)
    curses.init_pair(HL_PINK, 218, -1)

    # curses.init_pair(HL_YELLOW, 11, -1) # 11
    # curses.init_pair(HL_PASTEL_GREEN, 142, -1)

    curses.init_pair(HL_NORMAL, -1, -1)
