import curses

from utils.logger import *


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


class Control():
    def __init__(self):
        self.directory_brows = {}
        self.file_edit = {}
        self.file_management = {}
        self.tag_management = {}
        self.note_management = {}
        self.filter_management = {}
        # self.menu_brows = {} # TODO
        # self.user_input = {} # TODO
        # self.help_show = {} # TODO


    def get_function(self, env, key):
        dict_funcions = {}
        if env.is_filter_mode():
            dict_funcions = self.filter_management
        else:
            if env.is_brows_mode():
                dict_funcions = self.directory_brows
            elif env.is_view_mode():
                if env.file_edit_mode:
                    dict_funcions = self.file_edit
                else:
                    dict_funcions = self.file_management
            elif env.is_tag_mode():
                dict_funcions = self.tag_management
            elif env.is_notes_mode():
                dict_funcions = self.note_management

        if key in dict_funcions:
            return dict_funcions[key]
        return None


    def set_file_functions(self, control):
        file_functions = control['file_functions']
        edit_file_functions = control['edit_file_functions']
        manage_file_functions = control['manage_file_functions']

        file_keys = {}
        for str_fce, key in file_functions.items():
            fce = map_file_function(str_fce)
            if fce is not None:
                if isinstance(key,list):
                    for k in key:
                        file_keys[k] = fce
                else:
                    file_keys[key] = fce

        # control for file edit
        edit_keys = file_keys.copy()
        for str_fce, key in edit_file_functions.items():
            fce = map_file_function(str_fce)
            if fce is not None:
                if isinstance(key,list):
                    for k in key:
                        edit_keys[k] = fce
                else:
                    edit_keys[key] = fce

        # control for file management
        mgmt_keys = file_keys.copy()
        for str_fce, key in manage_file_functions.items():
            fce = map_file_function(str_fce)
            if fce is not None:
                if isinstance(key,list):
                    for k in key:
                        mgmt_keys[k] = fce
                else:
                    mgmt_keys[key] = fce

        self.file_edit = edit_keys
        self.file_management = mgmt_keys

    def set_brows_functions(self, control):
        brows_functions = control['brows_functions']
        keys = {}
        for str_fce, key in brows_functions.items():
            fce = map_brows_function(str_fce)
            if fce is not None:
                if isinstance(key,list):
                    for k in key:
                        keys[k] = fce
                else:
                    keys[key] = fce
        self.directory_brows = keys

    def set_tags_functions(self, control):
        tags_functions = control['tags_functions']
        keys = {}
        for str_fce, key in tags_functions.items():
            fce = map_tags_function(str_fce)
            if fce is not None:
                if isinstance(key,list):
                    for k in key:
                        keys[k] = fce
                else:
                    keys[key] = fce
        self.tag_management = keys

    def set_notes_functions(self, control):
        notes_functions = control['notes_functions']
        keys = {}
        for str_fce, key in notes_functions.items():
            fce = map_notes_function(str_fce)
            if fce is not None:
                if isinstance(key,list):
                    for k in key:
                        keys[k] = fce
                else:
                    keys[key] = fce
        self.note_management = keys

    def set_filter_functions(self, control):
        filter_functions = control['filter_functions']
        keys = {}
        for str_fce, key in filter_functions.items():
            fce = map_filter_function(str_fce)
            if fce is not None:
                if isinstance(key,list):
                    for k in key:
                        keys[k] = fce
                else:
                    keys[key] = fce
        self.filter_management = keys



def get_function_for_key(env, key):
    if key == curses.KEY_F1:
        return env.control.get_function(env, 'F1')
    elif key == curses.KEY_F2:
        return env.control.get_function(env, 'F2')
    elif key == curses.KEY_F3:
        return env.control.get_function(env, 'F3')
    elif key == curses.KEY_F4:
        return env.control.get_function(env, 'F4')
    elif key == curses.KEY_F5:
        return env.control.get_function(env, 'F5')
    elif key == curses.KEY_F6:
        return env.control.get_function(env, 'F6')
    elif key == curses.KEY_F7:
        return env.control.get_function(env, 'F7')
    elif key == curses.KEY_F8:
        return env.control.get_function(env, 'F8')
    elif key == curses.KEY_F9:
        return env.control.get_function(env, 'F9')
    elif key == curses.KEY_F10:
        return env.control.get_function(env, 'F10')
    elif key == curses.KEY_F11:
        return env.control.get_function(env, 'F11')
    elif key == curses.KEY_F12:
        return env.control.get_function(env, 'F12')
    elif key == 27:
        return env.control.get_function(env, 'ESC')
    elif key == curses.ascii.TAB:
        return env.control.get_function(env, 'TAB')
    elif key == curses.KEY_RESIZE:
        return RESIZE_WIN
        # return env.control.get_function(env, 'RESIZE')
    elif key == curses.KEY_UP:
        return env.control.get_function(env, 'UP')
    elif key == curses.KEY_DOWN:
        return env.control.get_function(env, 'DOWN')
    elif key == curses.KEY_LEFT:
        return env.control.get_function(env, 'LEFT')
    elif key == curses.KEY_RIGHT:
        return env.control.get_function(env, 'RIGHT')
    elif key == curses.KEY_DC:
        return env.control.get_function(env, 'DELETE')
    elif key == curses.KEY_BACKSPACE:
        return env.control.get_function(env, 'BACKSPACE')
    elif key == curses.ascii.NL:
        return env.control.get_function(env, 'ENTER')
    elif curses.ascii.isprint(key):
        char_key = chr(key)
        function = None
        # try to find some function for specitic ascii symbols
        if char_key == '\\':
            function = env.control.get_function(env, 'BACKSLASH')
        elif char_key in [str(i) for i in range(0,10)]:
            function = env.control.get_function(env, char_key) # number 0..10
        # ============>>> HERE YOU CAN ADD SPECIFIC SYMBOLS TO MATCH <<<============

        if function is None:
            # if there is no specific function, return general ASCII function
            return env.control.get_function(env, 'ASCII')
        else:
            return function
    if curses.ascii.ismeta(key):
        ctrl_key = curses.ascii.unctrl(key)
        if ctrl_key == '7' or hex(key) == "0x237":
            return env.control.get_function(env, 'CTRL+UP')
        elif ctrl_key == '^N' or hex(key) == "0x20e":
            return env.control.get_function(env, 'CTRL+DOWN')
    elif curses.ascii.iscntrl(key):
        ctrl_key = curses.ascii.unctrl(key)
        if ctrl_key == '^L':
            return env.control.get_function(env, 'CTRL+L')
        elif ctrl_key == '^N':
            return env.control.get_function(env, 'CTRL+N')
        elif ctrl_key == '^R':
            return env.control.get_function(env, 'CTRL+R')
        # ===============>>> HERE YOU CAN ADD CTRL KEYS TO MATCH <<<===============

    return None



""" mapping of functions from controls.yaml to intern representation """
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
        'quick_view_on_off': QUICK_VIEW_ON_OFF,
        'open_file': OPEN_FILE,
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

