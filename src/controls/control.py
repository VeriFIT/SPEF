import curses

from controls.functions import *
from utils.logger import *



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


    def get_function(self, env, key):
        dict_funcions = {}
        if env.is_user_input_mode():
            dict_funcions = self.user_input
        elif env.is_menu_mode():
            dict_funcions = self.menu_brows
        elif env.is_filter_mode():
            dict_funcions = self.filter_management
        elif env.is_brows_mode():
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

    def set_menu_functions(self, control):
        menu_functions = control['menu_functions']
        keys = {}
        for str_fce, key in menu_functions.items():
            fce = map_menu_function(str_fce)
            if fce is not None:
                if isinstance(key,list):
                    for k in key:
                        keys[k] = fce
                else:
                    keys[key] = fce
        self.menu_brows = keys

    def set_user_input_functions(self, control):
        user_input_functions = control['user_input_functions']
        keys = {}
        for str_fce, key in user_input_functions.items():
            fce = map_user_input_function(str_fce)
            if fce is not None:
                if isinstance(key,list):
                    for k in key:
                        keys[k] = fce
                else:
                    keys[key] = fce
        self.user_input = keys


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
        # https://asecuritysite.com/coding/asc2?val=512%2C768
        if hex(key) == "0x237" or ctrl_key == '7':
            return env.control.get_function(env, 'CTRL+UP')
        elif hex(key) == "0x20e" or ctrl_key == '^N':
            return env.control.get_function(env, 'CTRL+DOWN')
        elif hex(key) == "0x222":
            return env.control.get_function(env, 'CTRL+LEFT')
        elif hex(key) == "0x231":
            return env.control.get_function(env, 'CTRL+RIGHT')

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


