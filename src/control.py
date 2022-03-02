import curses

from utils.logger import *


""" file (edit/manage) control """
SHOW_HELP = 1
SAVE_FILE = 2
SHOW_OR_HIDE_TAGS = 3
SET_EDIT_FILE_MODE = 4
SHOW_OR_HIDE_LINE_NUMBERS = 5
SHOW_OR_HIDE_NOTE_HIGHLIGHT = 6
OPEN_NOTE_MANAGEMENT = 7
RELOAD_FILE_FROM_LAST_SAVE = 8
SHOW_TYPICAL_NOTES = 9
EXIT_PROGRAM = 10
SET_MANAGE_FILE_MODE = 11
CHANGE_FOCUS = 12
RESIZE_WIN = 13
CURSOR_UP = 14
CURSOR_DOWN = 15
CURSOR_LEFT = 16
CURSOR_RIGHT = 17
DELETE = 18
BACKSPACE = 19
PRINT_NEW_LINE = 20
PRINT_CHAR = 21
FILTER = 22
ADD_CUSTOM_NOTE = 23
ADD_TYPICAL_NOTE = 24
GO_TO_PREV_NOTE = 25
GO_TO_NEXT_NOTE = 26
RELOAD_ORIGINAL_BUFF = 27

""" directory browsing control """



class Control():
    def __init__(self):
        self.directory_brows = {}
        self.file_edit = {}
        self.file_management = {}
        self.tag_management = {}
        self.note_management = {}
        self.filter_management = {}
        self.menu_brows = {}
        self.user_input = {}
        self.help_show = {}


    def get_function(self, env, key):
        dict_funcions = {}
        # if env.filter_on:
            # dict_funcions = self.filter_management
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

        # log(str(dict_funcions))
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
