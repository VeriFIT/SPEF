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
        self.user_logs = {}

        self.filter_hint = {}
        self.brows_hint = {}
        self.view_hint = {}
        self.tag_hint = {}
        self.note_hint = {}
        self.logs_hint = {}


    def set_hints(self, env):
        data = []
        # filter
        filter_main_functions = {
            SHOW_HELP: "help",
            AGGREGATE_FILTER: "aggregate",
            REMOVE_FILTER: "remove all filters",
            EXIT_FILTER: "exit filter",
            EXIT_PROGRAM: "exit"}
        filter_dict_funcions = self.filter_management
        data.append(("F", filter_main_functions, filter_dict_funcions))

        # brows
        view_switch = "off" if env.quick_view else "on"
        logs_switch = "hide" if env.show_logs else "show"
        brows_main_functions = {
            SHOW_HELP: "help",
            OPEN_MENU: "menu",
            QUICK_VIEW_ON_OFF: f"quick view {view_switch}",
            SHOW_OR_HIDE_LOGS: f"{logs_switch} logs",
            OPEN_FILE: "edit",
            GO_TO_TAGS: "go to tags",
            DELETE_FILE: "delete",
            EXIT_PROGRAM: "exit"}
        brows_dict_funcions = self.directory_brows
        data.append(("B", brows_main_functions, brows_dict_funcions))

        # view
        tags_switch = "hide" if env.show_tags else "show"
        lines_switch = "hide" if env.line_numbers else "show"
        view_main_functions = {
            SHOW_HELP: "help",
            SAVE_FILE: "save",
            SHOW_OR_HIDE_TAGS: f"{tags_switch} tags",
            SHOW_OR_HIDE_LINE_NUMBERS: f"{lines_switch} lines",
            SHOW_OR_HIDE_NOTE_HIGHLIGHT: f"note highlight",
            OPEN_NOTE_MANAGEMENT: "note mgmt",
            RELOAD_FILE_FROM_LAST_SAVE: "reload",
            SHOW_TYPICAL_NOTES: "show typical notes",
            SET_MANAGE_FILE_MODE: "manage file",
            SET_EDIT_FILE_MODE: "edit file",
            EXIT_PROGRAM: "exit"}
        file_dict_funcions = self.file_edit.copy()
        file_dict_funcions.update(self.file_management)
        data.append(("V", view_main_functions, file_dict_funcions))

        # tags
        tag_main_functions = {
            SHOW_HELP: "help",
            EDIT_TAG: "edit tag",
            ADD_TAG: "new tag",
            DELETE_TAG: "delete",
            EXIT_PROGRAM: "exit"}
        tag_dict_funcions = self.tag_management
        data.append(("T", tag_main_functions, tag_dict_funcions))

        # notes
        typical_switch = "save as"
        if env.report is not None:
            if len(env.report.data) > 0 and len(env.report.data) >= env.windows.notes.cursor.row:
                if env.report.data[env.windows.notes.cursor.row].is_typical(env):
                    typical_switch = "unsave from"
        note_main_functions = {
            SHOW_HELP: "help",
            EDIT_NOTE: "edit note",
            SHOW_TYPICAL_NOTES: "show typical notes",
            GO_TO_NOTE: "go to",
            SAVE_AS_TYPICAL_NOTE: f"{typical_switch} typical",
            DELETE_NOTE: "delete",
            ADD_CUSTOM_NOTE: "add custom note",
            EXIT_NOTES: "exit note mgmt",
            EXIT_PROGRAM: "exit"}
        note_dict_funcions = self.note_management
        data.append(("N", note_main_functions, note_dict_funcions))

        # logs
        logs_main_functions = {
            SHOW_HELP: "help",
            OPEN_FILE: "open logs file",
            CLEAR_LOG: "clear logs file",
            EXIT_PROGRAM: "exit"}
        logs_dict_funcions = self.user_logs
        data.append(("L", logs_main_functions, logs_dict_funcions))


        for item in data:
            mode, main_functions, dict_funcions = item
            help_dict = {}
            if main_functions and dict_funcions:
                for fce, descr in main_functions.items():
                    key = None
                    for k, v in dict_funcions.items():
                        if fce == v:
                            key = k
                            break
                    if key:
                        help_dict[key] = descr
            if mode == "F":
                self.filter_hint = help_dict
            elif mode == "B":
                self.brows_hint = help_dict
            elif mode == "V":
                self.view_hint = help_dict
            elif mode == "T":
                self.tag_hint = help_dict
            elif mode == "N":
                self.note_hint = help_dict
            elif mode == "L":
                self.logs_hint = help_dict


    def get_hint_for_mode(self, env):
        if env.is_filter_mode():
            return self.filter_hint
        elif env.is_brows_mode():
            view_switch = "off" if env.quick_view else "on"
            logs_switch = "hide" if env.show_logs else "show"
            brows_dict_funcions = self.directory_brows
            brows_key, logs_key = None, None
            for k, v in brows_dict_funcions.items():
                if QUICK_VIEW_ON_OFF == v:
                    brows_key = k
                elif SHOW_OR_HIDE_LOGS == v:
                    logs_key = k
            if brows_key and logs_key:
                if brows_key in self.brows_hint:
                    self.brows_hint[brows_key] = f"quick view {view_switch}"
                if logs_key in self.brows_hint:
                    self.brows_hint[logs_key] = f"{logs_switch} logs"
            return self.brows_hint
        elif env.is_view_mode():
            tags_switch = "hide" if env.show_tags else "show"
            lines_switch = "hide" if env.line_numbers else "show"
            file_dict_funcions = self.file_edit.copy()
            file_dict_funcions.update(self.file_management)
            tag_key, line_key = None, None
            for k, v in file_dict_funcions.items():
                if SHOW_OR_HIDE_TAGS == v:
                    tag_key = k
                elif SHOW_OR_HIDE_LINE_NUMBERS == v:
                    line_key = k
            if tag_key and line_key:
                if tag_key in self.view_hint:
                    self.view_hint[tag_key] = f"{tags_switch} tags"
                if line_key in self.view_hint:
                    self.view_hint[line_key] = f"{lines_switch} lines"
            return self.view_hint
        elif env.is_tag_mode():
            return self.tag_hint
        elif env.is_notes_mode():
            typical_switch = "save as"
            if env.report is not None:
                if len(env.report.data) > 0 and len(env.report.data) >= env.windows.notes.cursor.row:
                    if env.report.data[env.windows.notes.cursor.row].is_typical(env):
                        typical_switch = "unsave from"
            note_dict_funcions = self.note_management
            note_key = None
            for k, v in note_dict_funcions.items():
                if SAVE_AS_TYPICAL_NOTE == v:
                    note_key = k
                    break
            if note_key and note_key in self.note_hint:
                self.note_hint[note_key] = f"{typical_switch} typical"
            return self.note_hint
        elif env.is_logs_mode():
            return self.logs_hint

        return None


    """ get function for key according to current mode """
    def get_function(self, env, key):
        dict_funcions = self.get_function_mapping_for_mode(env)
        if key in dict_funcions:
            return dict_funcions[key]
        return None


    def get_function_mapping_for_mode(self, env):
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
        elif env.is_logs_mode():
            dict_funcions = self.user_logs
        return dict_funcions


    def set_file_functions(self, control):
        file_functions = {}
        file_functions.update(control['general'])
        file_functions.update(control['file_functions'])
        file_functions.update(control['arrows'])
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
        brows_functions = {}
        brows_functions.update(control['general'])
        brows_functions.update(control['brows_functions'])
        brows_functions.update(control['arrows'])
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
        tags_functions = {}
        tags_functions.update(control['general'])
        tags_functions.update(control['tags_functions'])
        tags_functions.update(control['arrows'])
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
        notes_functions = {}
        notes_functions.update(control['general'])
        notes_functions.update(control['notes_functions'])
        notes_functions.update(control['arrows'])
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
        filter_functions = {}
        filter_functions.update(control['general'])
        filter_functions.update(control['filter_functions'])
        filter_functions.update(control['arrows'])
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
        menu_functions = {}
        menu_functions.update(control['general'])
        menu_functions.update(control['menu_functions'])
        menu_functions.update(control['arrows'])
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
        user_input_functions = {}
        user_input_functions.update(control['general'])
        user_input_functions.update(control['user_input_functions'])
        user_input_functions.update(control['arrows'])
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

    def set_user_logs_functions(self, control):
        user_logs_functions = {}
        user_logs_functions.update(control['general'])
        user_logs_functions.update(control['user_logs_functions'])
        user_logs_functions.update(control['arrows'])
        keys = {}
        for str_fce, key in user_logs_functions.items():
            fce = map_user_logs_function(str_fce)
            if fce is not None:
                if isinstance(key,list):
                    for k in key:
                        keys[k] = fce
                else:
                    keys[key] = fce
        self.user_logs = keys



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
        if char_key == '/':
            function = env.control.get_function(env, 'SLASH')
        elif char_key in [str(i) for i in range(0,10)]:
            function = env.control.get_function(env, char_key) # number 0..9
        elif char_key in "abcdefghijklmnopqrstuvwxyz":
            function = env.control.get_function(env, char_key)
            if function is None:
                function = env.control.get_function(env, 'a..z')
        elif char_key in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            function = env.control.get_function(env, char_key)
            if function is None:
                function = env.control.get_function(env, 'A..Z')
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
        elif ctrl_key == '^T':
            return env.control.get_function(env, 'CTRL+T')
        elif ctrl_key == '^O':
            return env.control.get_function(env, 'CTRL+O')
        # ===============>>> HERE YOU CAN ADD CTRL KEYS TO MATCH <<<===============

    return None


