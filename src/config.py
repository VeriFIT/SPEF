import os


from utils.logger import *


""" modes """
BROWS = 1
VIEW = 2
TAG = 3
EXIT = -1

PROJ_DIR = "subjectA/projectA"
# PROJ_DIR = "subject1/2021/project"



class Config:
    def __init__(self, left_screen, right_screen, down_screen, center_screen=None):
        self.left_screen = left_screen
        self.right_screen = right_screen
        self.down_screen = down_screen # for hint
        self.center_screen = center_screen
        self.right_up_screen = None
        self.right_down_screen = None

        """ view window """
        self.left_win = None
        self.right_win = None
        self.center_win = None
        self.right_up_win = None
        self.right_down_win = None

        self.mode = BROWS # start with browsing directory
        self.quick_view = True
        self.edit_allowed = False
        self.note_highlight = True
        self.line_numbers = None # None or str(number_of_lines_in_buffer)
        self.show_cached_files = False # files for tags and report

        self.file_to_open = None
        self.cwd = None # Directory(path, dirs, files)
        self.buffer = None # Buffer(path, lines)
        self.tags = None # Tags(path, data)
        self.report = None # Report(path, code_review)

        """ filter """
        self.filter = None # Filter()
        self.filtered_files = None # Directory(path, [], files)


    # TODO: get current project dir
    def get_project_path(self):
        return os.path.join(HOME, PROJ_DIR)

    def get_project_name(self):
        return PROJ_DIR

    def set_file_to_open(self, file_to_open):
        if self.file_to_open != file_to_open:
            self.file_to_open = file_to_open
            if self.edit_allowed:
                self.right_win.reset()
            else:
                self.right_up_win.reset()

    def get_screen_for_current_mode(self):
        if self.is_brows_mode():
            return self.left_screen, self.left_win
        if self.is_view_mode():
            if self.edit_allowed:
                return self.right_screen, self.right_win
            else:
                return self.right_up_screen, self.right_up_win
        if self.is_tag_mode():
            return self.right_down_screen, self.right_down_win

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
        self.left_win = win
        self.cwd = cwd

    def update_viewing_data(self, win, buffer, report=None):
        if self.edit_allowed:
            self.right_win = win
        else:
            self.right_up_win = win
        self.buffer = buffer
        if report:
            self.report = report

    def update_tagging_data(self, win, tags):
        self.right_down_win = win
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
