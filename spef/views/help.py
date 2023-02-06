import curses
import curses.ascii

import spef.controls.functions as func
from spef.utils.printing import parse_line_into_sublines, rewrite_all_wins, print_help
from spef.utils.screens import resize_all
from spef.utils.logger import ESC


# return number of lines needed to print given buffer
# buff = {'key': 'line', ...}
# space (number) = length of space between key and line
def calculate_buff_len_lines(buff, space, max_cols, start_at=None, stop_at=None):
    total_len = 0
    for idx, key in enumerate(buff):
        if start_at is not None and idx < start_at:
            continue
        if stop_at is not None and idx >= stop_at:
            return total_len
        free_space = max_cols - len(key) - space
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
            shifted = calculate_buff_len_lines(
                actions, 3, max_cols, stop_at=win.row_shift
            )
            if actions_len >= shifted + max_rows - shift:
                win.row_shift += 1
        elif curses.ascii.ismeta(key):
            """CTRL + LEFT / CTRL + RIGHT"""
            # https://asecuritysite.com/coding/asc2?val=512%2C768
            if hex(key) == "0x222" or hex(key) == "0x231":
                if hex(key) == "0x222":  # move left
                    if position == 2:
                        position = 1
                    elif position == 3:
                        position = 2
                    win.set_position(position, screen)
                elif hex(key) == "0x231":  # move right
                    if position == 1:
                        position = 2
                    elif position == 2:
                        position = 3
                    win.set_position(position, screen)
                rewrite_all_wins(env)
        elif exit_key == []:  # if exit key is empty, exit on any key
            rewrite_all_wins(env)
            return env, key


def get_help(env):
    dict_functions = env.control.get_function_mapping_for_mode(env)

    actions = {}
    for key, function in dict_functions.items():
        if function in [
            func.CURSOR_UP,
            func.CURSOR_DOWN,
            func.CURSOR_LEFT,
            func.CURSOR_RIGHT,
        ]:
            key = "Arrows"
            function = "Arrows"
        elif function in [func.DELETE_CHAR, func.BACKSPACE_CHAR]:
            key = "Delete, backspace"
            function = "Del"
        elif key == "SLASH":
            key = "/"
        description = get_description_for_fce(env, function)
        if description is not None:
            actions[key] = description

    same_value = None
    succ = False
    if "1" in actions:
        same_value = actions["1"]
        succ = True

    if same_value:
        for i in range(2, 10):
            succ = False
            i = str(i)
            if i in actions:
                if same_value == actions[i]:
                    succ = True

    if same_value and succ:
        new = {}
        for key, value in actions.items():
            if key in "123456789":
                new["1..9"] = same_value
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
            func.SHOW_HELP: "show this user help",
            func.EXIT_PROGRAM: "exit program",
            func.EXIT_USER_INPUT: "exit user input without saving",
            func.BASH_SWITCH: "switch to bash",
            "Arrows": "move cursor in user input",
            "Del": "delete symbol in user input",
            func.PRINT_CHAR: "insert symbol in user input",
            func.SAVE_INPUT: "save user input and exit",
            func.MOVE_LEFT: "move window to the left",
            func.MOVE_RIGHT: "move window to the right",
        }
    elif env.is_menu_mode():
        descr_dir = {
            func.SHOW_HELP: "show this user help",
            func.EXIT_PROGRAM: "exit program",
            func.EXIT_MENU: "exit menu",
            func.BASH_SWITCH: "switch to bash",
            "Arrows": "brows between menu options",
            func.SAVE_OPTION: "save current selected option",
            func.SELECT_BY_IDX: "save option by index",
            func.SELECT_OPTION: "select multiple options",
            func.MOVE_LEFT: "move window to the left",
            func.MOVE_RIGHT: "move window to the right",
        }
    elif env.is_filter_mode():
        descr_dir = {
            func.SHOW_HELP: "show this user help",
            func.AGGREGATE_FILTER: "aggregate by same tags file",
            func.REMOVE_FILTER: "remove all filters",
            func.EXIT_PROGRAM: "exit program",
            func.EXIT_FILTER: "exit filter management",
            func.BASH_SWITCH: "switch to bash",
            "Arrows": "move cursor in user input",
            "Del": "delete symbol in user input",
            func.PRINT_CHAR: "insert symbol in user input",
            func.SAVE_FILTER: "set filter and exit filter management",
        }
    elif env.is_brows_mode():
        descr_dir = {
            func.SHOW_HELP: "show this user help",
            func.OPEN_MENU: "open menu with other functions",
            func.QUICK_VIEW_ON_OFF: "set quick view mode on/off",
            func.OPEN_FILE: "open file for edit",
            func.GO_TO_TAGS: "change focus to tags",
            func.SHOW_OR_HIDE_CACHED_FILES: "show/hide cached files (tags, report)",
            func.SHOW_OR_HIDE_LOGS: "show/hide logs for user",
            func.DELETE_FILE: "delete selected file",
            func.EXIT_PROGRAM: "exit program",
            func.CHANGE_FOCUS: "change focus to file view/edit",
            func.BASH_SWITCH: "switch to bash",
            func.FILTER: "set filter by path",
            "Arrows": "brows between files and dirs",
        }
    elif env.is_view_mode():
        if env.show_tags:
            tab_action = "tag management"
        elif env.show_notes:
            tab_action = "note management"
        else:
            tab_action = "directory browsing"
        descr_dir = {
            func.SHOW_HELP: "show this user help",
            func.SAVE_FILE: "save file changes",
            func.SHOW_OR_HIDE_TAGS: "show/hide tags",
            func.SHOW_OR_HIDE_LINE_NUMBERS: "show/hide line numbers",
            func.SHOW_OR_HIDE_NOTE_HIGHLIGHT: "show/hide note highlight",
            func.OPEN_NOTE_MANAGEMENT: "open note management",
            func.RELOAD_FILE_FROM_LAST_SAVE: "reload file content from last save",
            func.SHOW_TYPICAL_NOTES: "show typical notes",
            func.EXIT_PROGRAM: "exit program",
            func.CHANGE_FOCUS: f"change focus to {tab_action}",
            func.BASH_SWITCH: "switch to bash",
            func.FILTER: "set filter by content",
            "Arrows": "move cursor in file content",
            func.SET_MANAGE_FILE_MODE: "set manage file mode",
            func.SET_EDIT_FILE_MODE: "set edit file mode",
            func.ADD_CUSTOM_NOTE: "add custom note to current line",
            func.ADD_TYPICAL_NOTE: "add typical note to current line",
            func.PRINT_CHAR: "insert symbol in file on current cursor position",
            func.PRINT_NEW_LINE: "insert new line in file on current cursor position",
            "Del": "delete symbol in file on current cursor position",
            func.GO_TO_PREV_NOTE: "jump to line with previous note in file",
            func.GO_TO_NEXT_NOTE: "jump to line with next note in file",
            func.RELOAD_ORIGINAL_BUFF: "reload file content from original buffer",
        }
        if env.editing_test_file:
            descr_dir.update(
                {
                    func.SHOW_SUPPORTED_DATA: "show supported bash functions for 'dotest.sh'"
                }
            )
        elif env.editing_report_template:
            descr_dir.update(
                {func.SHOW_SUPPORTED_DATA: "show supported data for report template"}
            )
    elif env.is_tag_mode():
        descr_dir = {
            func.SHOW_HELP: "show this user help",
            func.EDIT_TAG: "edit current tag",
            func.ADD_TAG: "create new tag",
            func.OPEN_TAG_FILE: "open file with tags for edit",
            func.DELETE_TAG: "delete current tag",
            func.EXIT_PROGRAM: "exit program",
            func.CHANGE_FOCUS: "change focus to directory browsing",
            func.BASH_SWITCH: "switch to bash",
            func.FILTER: "set filter by tag",
            "Arrows": "brows between tags",
        }
    elif env.is_notes_mode():
        descr_dir = {
            func.SHOW_HELP: "show this user help",
            func.EDIT_NOTE: "edit current note",
            func.SHOW_TYPICAL_NOTES: "show typical notes",
            func.GO_TO_NOTE: "go to current note in file",
            func.SAVE_AS_TYPICAL_NOTE: "save note as typical",
            func.DELETE_NOTE: "delete current note",
            func.EXIT_PROGRAM: "exit program",
            func.EXIT_NOTES: "exit note management",
            func.CHANGE_FOCUS: "change focus to file view/edit",
            func.BASH_SWITCH: "switch to bash",
            "Arrows": "brows between notes",
            func.ADD_CUSTOM_NOTE: "add custom note",
            func.ADD_TYPICAL_NOTE: "add typical notes",
        }

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
