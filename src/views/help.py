
import curses
import curses.ascii

from controls.functions import *
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

    if actions is None:
        return env, None

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y
    actions_len = calculate_buff_len_lines(actions, 3, max_cols)

    rewrite_all_wins(env)

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
    dict_functions = env.control.get_function_mapping_for_mode(env)

    actions = {}
    for key, function in dict_functions.items():
        if function in [CURSOR_UP, CURSOR_DOWN, CURSOR_LEFT, CURSOR_RIGHT]:
            key = "Arrows"
            function = "Arrows"
        elif function in [DELETE_CHAR, BACKSPACE_CHAR]:
            key = "Delete, backspace"
            function = "Del"
        elif key == 'SLASH':
            key = "/"
        description = get_description_for_fce(env, function)
        if description is not None:
            actions[key] = description

    same_value = None
    succ = False
    if '1' in actions:
        same_value = actions['1']
        succ = True

    if same_value:
        for i in range(2,10):
            succ = False
            i = str(i)
            if i in actions:
                if same_value == actions[i]:
                    succ = True

    if same_value and succ:
        new = {}
        for key, value in actions.items():
            if key in "123456789":
                new['1..9'] = same_value
            else:
                new[key] = value
        actions = new

    mode = get_description_for_mode(env)

    exit_message = "Press ESC or F1 to hide user help."
    title = f"*** USER HELP FOR {mode} ***"
    return exit_message, title, actions


def get_description_for_fce(env, fce):
    descr_dir = {}

    if env.is_user_input_mode():
        descr_dir = {
        SHOW_HELP: "show this user help",    
        EXIT_PROGRAM: "exit program",
        EXIT_USER_INPUT: "exit user input without saving",
        BASH_SWITCH: "switch to bash",
        "Arrows": "move cursor in user input",
        "Del": "delete symbol in user input",
        PRINT_CHAR: "insert symbol in user input",
        SAVE_INPUT: "save user input and exit",
        MOVE_LEFT: "move window to the left",
        MOVE_RIGHT: "move window to the right"}
    elif env.is_menu_mode():
        descr_dir = {
        SHOW_HELP: "show this user help",    
        EXIT_PROGRAM: "exit program",
        EXIT_MENU: "exit menu",
        BASH_SWITCH: "switch to bash",
        "Arrows": "brows between menu options",
        SAVE_OPTION: "save current selected option",
        SELECT_BY_IDX: "save option by index",
        SELECT_OPTION: "select multiple options",
        MOVE_LEFT: "move window to the left",
        MOVE_RIGHT: "move window to the right"}
    elif env.is_filter_mode():
        descr_dir = {
        SHOW_HELP: "show this user help",
        AGGREGATE_FILTER: "aggregate by same tags file",
        REMOVE_FILTER: "remove all filters",
        EXIT_PROGRAM: "exit program",
        EXIT_FILTER: "exit filter management",
        BASH_SWITCH: "switch to bash",
        "Arrows": "move cursor in user input",
        "Del": "delete symbol in user input",
        PRINT_CHAR: "insert symbol in user input",
        SAVE_FILTER: "set filter and exit filter management"}
    elif env.is_brows_mode():
        descr_dir = {
        SHOW_HELP: "show this user help",
        OPEN_MENU: "open menu with other functions",
        QUICK_VIEW_ON_OFF: "set quick view mode on/off",
        OPEN_FILE: "open file for edit",
        GO_TO_TAGS: "change focus to tags",
        SHOW_OR_HIDE_CACHED_FILES: "show/hide cached files (tags, report)",
        SHOW_OR_HIDE_LOGS: "show/hide logs for user",
        DELETE_FILE: 'delete selected file',
        EXIT_PROGRAM: "exit program",
        CHANGE_FOCUS: "change focus to file view/edit",
        BASH_SWITCH: "switch to bash",
        FILTER: "set filter by path",
        "Arrows": "brows between files and dirs"}
    elif env.is_view_mode():
        if env.show_tags:
            tab_action = "tag management"
        elif env.show_notes:
            tab_action = "note management"
        else:
            tab_action = "directory browsing"
        descr_dir = {
        SHOW_HELP: "show this user help",
        SAVE_FILE: "save file changes",
        SHOW_OR_HIDE_TAGS: "show/hide tags",
        SHOW_OR_HIDE_LINE_NUMBERS: "show/hide line numbers",
        SHOW_OR_HIDE_NOTE_HIGHLIGHT: "show/hide note highlight",
        OPEN_NOTE_MANAGEMENT: "open note management",
        RELOAD_FILE_FROM_LAST_SAVE: "reload file content from last save",
        SHOW_TYPICAL_NOTES: "show typical notes",
        EXIT_PROGRAM: "exit program",
        CHANGE_FOCUS: f"change focus to {tab_action}",
        BASH_SWITCH: "switch to bash",
        FILTER: "set filter by content",
        "Arrows": "move cursor in file content",
        SET_MANAGE_FILE_MODE: "set manage file mode",
        SET_EDIT_FILE_MODE: "set edit file mode",
        ADD_CUSTOM_NOTE: "add custom note to current line",
        ADD_TYPICAL_NOTE: "add typical note to current line",
        PRINT_CHAR: "insert symbol in file on current cursor position",
        PRINT_NEW_LINE: "insert new line in file on current cursor position",
        "Del": "delete symbol in file on current cursor position",
        GO_TO_PREV_NOTE: "jump to line with previous note in file",
        GO_TO_NEXT_NOTE: "jump to line with next note in file",
        RELOAD_ORIGINAL_BUFF: "reload file content from original buffer"}
        if env.editing_test_file:
            descr_dir.update({SHOW_SUPPORTED_DATA: "show supported bash functions for 'dotest.sh'"})
        elif env.editing_report_template:
            descr_dir.update({SHOW_SUPPORTED_DATA: "show supported data for report template"})
    elif env.is_tag_mode():
        descr_dir = {
        SHOW_HELP: "show this user help",
        EDIT_TAG: "edit current tag",
        ADD_TAG: "create new tag",
        OPEN_TAG_FILE: "open file with tags for edit",
        DELETE_TAG: "delete current tag",
        EXIT_PROGRAM: "exit program",
        CHANGE_FOCUS: "change focus to directory browsing",
        BASH_SWITCH: "switch to bash",
        FILTER: "set filter by tag",
        "Arrows": "brows between tags"}
    elif env.is_notes_mode():
        descr_dir = {
        SHOW_HELP: "show this user help",
        EDIT_NOTE: "edit current note",
        SHOW_TYPICAL_NOTES: "show typical notes",
        GO_TO_NOTE: "go to current note in file",
        SAVE_AS_TYPICAL_NOTE: "save note as typical",
        DELETE_NOTE: "delete current note",
        EXIT_PROGRAM: "exit program",
        EXIT_NOTES: "exit note management",
        CHANGE_FOCUS: "change focus to file view/edit",
        BASH_SWITCH: "switch to bash",
        "Arrows": "brows between notes",
        ADD_CUSTOM_NOTE: "add custom note",
        ADD_TYPICAL_NOTE: "add typical notes"}

    if fce in descr_dir:
        return descr_dir[fce]
    return None


def get_description_for_mode(env):
    mode = ""
    if env.is_user_input_mode():
        mode = "USER INPUT"
    elif env.is_menu_mode():
        mode = "MENU BROWSING"
    elif env.is_filter_mode():
        mode = "FILTER MANAGEMENT"
    elif env.is_brows_mode():
        mode = "DIRECTORY BROWSING"
    elif env.is_view_mode():
        mode = "FILE EDIT"
    elif env.is_tag_mode():
        mode = "TAG MANAGEMENT"
    elif env.is_notes_mode():
        mode = "NOTES MANAGEMENT"
    return mode
