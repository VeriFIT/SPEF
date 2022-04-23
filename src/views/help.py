
import curses
import curses.ascii


from modules.directory import Directory
from modules.window import Window
from modules.buffer import UserInput

from utils.printing import *
from utils.screens import *
from utils.logger import *

# return number of lines needed to print given buffer
# buff = {'key': 'line', ...}
# space (number) = length of space between key and line
def calculate_buff_len_lines(buff, space, max_cols, start_at=None, stop_at=None):
    total_len = 0
    for idx, key in enumerate(buff):
        if start_at is not None and idx<start_at:
            continue
        if stop_at is not None and idx>=stop_at:
            return total_len
        free_space = max_cols-len(key)-space
        line = buff[key]
        if len(line) > free_space:
            sublines = parse_line_into_sublines(line, free_space)
            total_len += len(sublines)
        else:
            total_len += 1
    return total_len



""" custom_help = (exit_message, title, dictionary)"""
def show_help(stdscr, env, custom_help=None, exit_key=None):
    curses.curs_set(0)

    screen, win = env.get_center_win(reset=True)
    position = win.position

    if exit_key is None:
        exit_key = [curses.KEY_F1, ESC]

    if custom_help is None:
        exit_mess, title, actions = get_help(env)
    else:
        exit_mess = custom_help[0]
        title = custom_help[1]
        actions = custom_help[2]


    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y
    actions_len = calculate_buff_len_lines(actions, 3, max_cols)

    while True:
        max_cols = win.end_x - win.begin_x
        max_rows = win.end_y - win.begin_y

        """ print help """
        print_help(screen, win, env, exit_mess, title, actions)
        # print_help(screen, max_cols, max_rows, env, custom_help=custom_help)

        key = stdscr.getch()

        if key in exit_key or key == curses.KEY_F10:
            rewrite_all_wins(env)
            return env, key
        elif key == curses.KEY_RESIZE:
            env = resize_all(stdscr, env)
            screen, win = env.get_center_win()
            win.reset()
            win.set_position(position, screen)
            rewrite_all_wins(env)
            max_cols = win.end_x - win.begin_x
            max_rows = win.end_y - win.begin_y
            actions_len = calculate_buff_len_lines(actions, 3, max_cols)
        # =================== ARRROWS ===================
        elif key == curses.KEY_UP:
            if win.row_shift > 0:
                win.row_shift -= 1
        elif key == curses.KEY_DOWN:
            shift = (1 if exit_mess else 0) + (1 if title else 0)
            shifted = calculate_buff_len_lines(actions, 3, max_cols, stop_at=win.row_shift)
            if actions_len >= shifted + max_rows - shift:
                win.row_shift += 1
        elif curses.ascii.ismeta(key):
            """ CTRL + LEFT / CTRL + RIGHT """
            # https://asecuritysite.com/coding/asc2?val=512%2C768
            if hex(key) == "0x222" or hex(key) == "0x231":
                if hex(key) == "0x222": # move left
                    if position == 2:
                        position = 1
                    elif position == 3:
                        position = 2
                    win.set_position(position, screen)
                elif hex(key) == "0x231": # move right
                    if position == 1:
                        position = 2
                    elif position == 2:
                        position = 3
                    win.set_position(position, screen)
                rewrite_all_wins(env)
        elif exit_key == []: # if exit key is empty, exit on any key
            rewrite_all_wins(env)
            return env, key

def get_help(env):
    mode = ""
    if env.is_filter_mode():
        mode = "FILTER MANAGEMENT"
        actions = {
        "F1": "show this user help",
        "F4": "aggregate by same tags file",
        "F8": "delete/remove all filters",
        "F10": "exit program",
        "ESC": "exit filter management",
        "Arrows": "move cursor in user input",
        "Delete, Backspace": "delete symbol in user input",
        "Ascii character": "insert symbol in user input",
        "Enter": "set filter and exit filter management"}
    elif env.is_brows_mode():
        mode = "DIRECTORY BROWSING"
        actions = {
        "F1": "show this user help",
        "F2": "open menu with other functions",
        "F3": "set quick view mode on/off",
        "F4": "opent file for edit",
        "F6": "show/hide cached files (tags, report)",
        "F9": "set filter by path",
        "F10": "exit program",
        "TAB": "change focus to file view or edit",
        "Arrows": "brows between files and dirs"}
    elif env.is_view_mode():
        if env.show_tags:
            tab_action = "change focus to tag management"
        elif env.show_notes:
            tab_action = "change focus to note management"
        else:
            tab_action = "change focus to directory browsing"

        mode = "FILE EDIT"
        actions = {
        "F1": "show this user help",
        "F2": "save file changes",
        "F3": "change to file view/tag mode"}
        if env.editing_test_file:
            actions.update({"F4": "show supported bash functions for 'dotest.sh'"})
        actions.update({
        "F5": "show/hide line numbers",
        "F6": "show/hide note highlight",
        "F7": "open note management",
        "F8": "reload file content from last save",
        "F9": "set filter by content",
        "F10": "exit program",
        "TAB": f"{tab_action}",
        "Arrows": "move cursor in file content",
        "Delete, Backspace": "delete symbol in file on current cursor position",
        "Ascii character": "insert symbol in file on current cursor position",
        "Enter": "insert new line in file on current cursor position",
        "CTRL + Up/Down": "jump to prev/next line with note in file",
        "CTRL + L": "reload file content from original buffer",
        "CTRL + R": "remove all notes on current line"})
    elif env.is_tag_mode():
        mode = "TAG MANAGEMENT"
        actions = {
        "F1": "show this user help",
        "F2": "edit current tag",
        "F3": "create new tag",
        "F4": "open file with tags for edit",
        "F8": "delete current tag",
        "F9": "set filter by tag",
        "F10": "exit program",
        "TAB": "change focus to directory browsing",
        "Arrows": "brows between tags"}
    elif env.is_notes_mode():
        mode = "NOTES MANAGEMENT"
        actions = {
        "F1": "show this user help",
        "F2": "edit current note",
        "F3": "create new note",
        "F4": "insert note from saved (typical) notes",
        "F5": "go to current note in file",
        "F6": "save note as typical",
        "F8": "delete current note",
        "F10": "exit program",
        "ESC": "exit note management",
        "TAB": "change focus to file view or edit",
        "Arrows": "brows between notes"}
    else:
        screen.refresh()
    exit_message = "Press ESC or F1 to hide user help."
    title = f"*** USER HELP FOR {mode} ***"

    return exit_message, title, actions
