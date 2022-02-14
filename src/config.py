import os
import yaml

from utils.logger import *


""" modes """
BROWS = 1
VIEW = 2
TAG = 3
EXIT = -1

PROJ_DIR = "subjectA/projectA"
# PROJ_DIR = "subject1/2021/project"


""" current framework environment """
class Environment:
    def __init__(self, screens, windows, conf):

        """ screens and windows """
        self.screens = screens
        self.windows = windows

        self.win_left_edge, self.win_right_edge = conf['window']['left_edge'], conf['window']['right_edge']
        self.win_top_edge, self.win_bottom_edge = conf['window']['top_edge'], conf['window']['bottom_edge']
        self.windows.set_edges(self.win_left_edge, self.win_right_edge, self.win_top_edge, self.win_bottom_edge)
        self.windows.center.position = conf['window']['position']


        """ environment """
        self.mode = conf['env']['mode']
        self.quick_view = conf['env']['quick_view']
        self.edit_allowed = conf['env']['edit_allowed']
        self.note_highlight = conf['env']['note_highlight']
        self.show_cached_files = conf['env']['show_cached_files'] # files for tags and report

        self.tab_size = conf['editor']['tab_size']
        self.messages = conf['messages'] # {'empty_path_filter': txt, 'empty_tag_filter': txt, ... }

        self.show_menu = False
        self.line_numbers = None # None or str(number_of_lines_in_buffer)

        self.file_to_open = None
        self.cwd = None # Directory(path, dirs, files)
        self.buffer = None # Buffer(path, lines)
        self.tags = None # Tags(path, data)
        self.report = None # Report(path, code_review)

        """ filter """
        self.filter = None # Filter()
        self.filtered_files = None # Directory(path, [], files)


    def get_all_screens(self):
        screens = {"LS": self.screens.left, "RS": self.screens.right, "DS": self.screens.down,
                "CS": self.screens.center, "RUS": self.screens.right_up, "RDS": self.screens.right_down}
        return screens

    def get_visible_screens(self):
        screens = {"LS": self.screens.left, "RS": self.screens.right, "DS": self.screens.down} # main screens
        if not self.edit_allowed:
            screens["RUS"] = self.screens.right_up
            screens["RDS"] = self.screens.right_down
        if self.show_menu:
            screens["CS"] = self.screens.center
        return screens


    # TODO: get current project dir
    def get_project_path(self):
        return os.path.join(HOME, PROJ_DIR)

    def get_project_name(self):
        return PROJ_DIR

    def set_file_to_open(self, file_to_open):
        if self.file_to_open != file_to_open:
            self.file_to_open = file_to_open
            if self.edit_allowed:
                self.windows.right.reset()
            else:
                self.windows.right_up.reset()
            self.windows.right_down.reset_shifts()
            self.windows.right_down.set_cursor(0,0)


    def get_screen_for_current_mode(self):
        if self.is_brows_mode():
            return self.screens.left, self.windows.left
        if self.is_view_mode():
            if self.edit_allowed:
                return self.screens.right, self.windows.right
            else:
                return self.screens.right_up, self.windows.right_up
        if self.is_tag_mode():
            return self.screens.right_down, self.windows.right_down

    """ filter """
    def filter_not_empty(self):
        if self.filter is not None:
            return not self.filter.is_empty()
        else:
            return False

    def path_filter_on(self):
        if self.filter is not None:
            if self.filter.path:
                return True
        return False

    def content_filter_on(self):
        if self.filter is not None:
            if self.filter.content:
                return True
        return False

    def tag_filter_on(self):
        if self.filter is not None:
            if self.filter.tag:
                return True
        return False

    """ update data """
    def update_browsing_data(self, win, cwd):
        self.windows.left = win
        self.cwd = cwd

    def update_viewing_data(self, win, buffer, report=None):
        if self.edit_allowed:
            self.windows.right = win
        else:
            self.windows.right_up = win
        self.buffer = buffer
        if report:
            self.report = report

    def update_tagging_data(self, win, tags):
        self.windows.right_down = win
        self.tags = tags


    def enable_file_edit(self):
        self.edit_allowed = True
        self.quick_view = False

    def disable_file_edit(self):
        self.edit_allowed = False

    def disable_line_numbers(self):
        self.line_numbers = None

    def enable_line_numbers(self, buffer):
        self.line_numbers = str(len(buffer))


    """ set mode """
    def set_brows_mode(self):
        self.mode = BROWS

    def set_view_mode(self):
        self.mode = VIEW

    def set_tag_mode(self):
        self.mode = TAG

    def set_exit_mode(self):
        self.mode = EXIT

    """ check mode """
    def is_brows_mode(self):
        return self.mode == BROWS

    def is_view_mode(self):
        return self.mode == VIEW

    def is_tag_mode(self):
        return self.mode == TAG

    def is_exit_mode(self):
        return self.mode == EXIT
