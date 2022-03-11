# functions identification

""" file (edit/manage) control """
EXIT_PROGRAM = 1
CHANGE_FOCUS = 2
RESIZE_WIN = 3
SHOW_HELP = 4
FILTER = 5

CURSOR_UP = 6
CURSOR_DOWN = 7
CURSOR_LEFT = 8
CURSOR_RIGHT = 9

SET_EDIT_FILE_MODE = 10
SET_MANAGE_FILE_MODE = 11
SHOW_OR_HIDE_TAGS = 12
SHOW_OR_HIDE_LINE_NUMBERS = 13
SHOW_OR_HIDE_NOTE_HIGHLIGHT = 14
SHOW_TYPICAL_NOTES = 15
OPEN_NOTE_MANAGEMENT = 16
ADD_CUSTOM_NOTE = 17
ADD_TYPICAL_NOTE = 18
GO_TO_PREV_NOTE = 19
GO_TO_NEXT_NOTE = 20
RELOAD_FILE_FROM_LAST_SAVE = 21
RELOAD_ORIGINAL_BUFF = 22

DELETE = 23
BACKSPACE = 24
PRINT_NEW_LINE = 25
PRINT_CHAR = 26
SAVE_FILE = 27


""" directory browsing control """
QUICK_VIEW_ON_OFF = 100
OPEN_FILE = 101
OPEN_MENU = 102
ADD_PROJECT = 103
DELETE_FILE = 104

""" tag management control """
EDIT_TAG = 200
ADD_TAG = 201
DELETE_TAG = 202
OPEN_TAG_FILE = 203

""" note management control """
EXIT_NOTES = 300
EDIT_NOTE = 301
GO_TO_NOTE = 302
SAVE_AS_TYPICAL_NOTE = 303
DELETE_NOTE = 304

""" filter management control """
EXIT_FILTER = 400
SAVE_FILTER = 401
REMOVE_FILTER = 402

""" menu control """
EXIT_MENU = 500
SAVE_OPTION = 501
MOVE_LEFT = 502
MOVE_RIGHT = 503

""" user input control """
EXIT_USER_INPUT = 600
SAVE_INPUT = 601




""" mapping of functions from controls.yaml to intern representation of function id """
def map_file_function(str_fce):
    functions = {
        'show_help': SHOW_HELP,
        'save_file': SAVE_FILE,
        'show_or_hide_tags': SHOW_OR_HIDE_TAGS,
        'set_edit_file_mode': SET_EDIT_FILE_MODE,
        'show_or_hide_line_numbers': SHOW_OR_HIDE_LINE_NUMBERS,
        'show_or_hide_note_highlight': SHOW_OR_HIDE_NOTE_HIGHLIGHT,
        'open_note_management': OPEN_NOTE_MANAGEMENT,
        'reload_file_from_last_save': RELOAD_FILE_FROM_LAST_SAVE,
        'show_typical_notes': SHOW_TYPICAL_NOTES,
        'exit_program': EXIT_PROGRAM,
        'set_manage_file_mode': SET_MANAGE_FILE_MODE,
        'change_focus': CHANGE_FOCUS,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'cursor_left': CURSOR_LEFT,
        'cursor_right': CURSOR_RIGHT,
        'delete': DELETE,
        'backspace': BACKSPACE,
        'print_new_line': PRINT_NEW_LINE,
        'print_char': PRINT_CHAR,
        'filter': FILTER,
        'add_custom_note': ADD_CUSTOM_NOTE,
        'add_typical_note': ADD_TYPICAL_NOTE,
        'go_to_prev_note': GO_TO_PREV_NOTE,
        'go_to_next_note': GO_TO_NEXT_NOTE,
        'reload_original_buff': RELOAD_ORIGINAL_BUFF}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_brows_function(str_fce):
    functions = {
        'show_help': SHOW_HELP,
        'open_menu': OPEN_MENU,
        'quick_view_on_off': QUICK_VIEW_ON_OFF,
        'open_file': OPEN_FILE,
        'delete_file': DELETE_FILE,
        'change_focus': CHANGE_FOCUS,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'cursor_left': CURSOR_LEFT,
        'cursor_right': CURSOR_RIGHT,
        'filter': FILTER,
        'exit_program': EXIT_PROGRAM}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_tags_function(str_fce):
    functions = {
        'show_help': SHOW_HELP,
        'edit_tag': EDIT_TAG,
        'add_tag': ADD_TAG,
        'delete_tag': DELETE_TAG,
        'open_tag_file': OPEN_TAG_FILE,
        'change_focus': CHANGE_FOCUS,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'filter': FILTER,
        'exit_program': EXIT_PROGRAM}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_notes_function(str_fce):
    functions = {
        'show_help': SHOW_HELP,
        'edit_note': EDIT_NOTE,
        'add_custom_note': ADD_CUSTOM_NOTE,
        'add_typical_note': ADD_TYPICAL_NOTE,
        'go_to_note': GO_TO_NOTE,
        'save_as_typical_note': SAVE_AS_TYPICAL_NOTE,
        'delete_note': DELETE_NOTE,
        'exit_program': EXIT_PROGRAM,
        'exit_notes': EXIT_NOTES,
        'change_focus': CHANGE_FOCUS,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_filter_function(str_fce):
    functions = {
        'show_help': SHOW_HELP,
        'remove_filter': REMOVE_FILTER,
        'exit_program': EXIT_PROGRAM,
        'exit_filter': EXIT_FILTER,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'cursor_left': CURSOR_LEFT,
        'cursor_right': CURSOR_RIGHT,
        'resize_win': RESIZE_WIN,
        'delete': DELETE,
        'backspace': BACKSPACE,
        'print_char': PRINT_CHAR,
        'save_filter': SAVE_FILTER}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_menu_function(str_fce):
    functions = {
        'exit_program': EXIT_PROGRAM,
        'exit_menu': EXIT_MENU,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'save_option': SAVE_OPTION,
        'move_left': MOVE_LEFT,
        'move_right': MOVE_RIGHT}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_user_input_function(str_fce):
    functions = {
        'exit_program': EXIT_PROGRAM,
        'exit_user_input': EXIT_USER_INPUT,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'cursor_left': CURSOR_LEFT,
        'cursor_right': CURSOR_RIGHT,
        'delete': DELETE,
        'backspace': BACKSPACE,
        'save_input': SAVE_INPUT,
        'print_char': PRINT_CHAR,
        'move_left': MOVE_LEFT,
        'move_right': MOVE_RIGHT}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None
