from logger import *

""" modes """
BROWS = 1
VIEW = 2
TAG = 3
EXIT = -1


class Config:
    def __init__(self, left_screen, right_screen, down_screen):
        self.left_screen = left_screen
        self.right_screen = right_screen
        self.down_screen = down_screen # for hint
        self.right_up_screen = None
        self.right_down_screen = None

        """ view window """
        self.left_win = None
        self.right_win = None
        self.right_up_win = None
        self.right_down_win = None

        """ coloring """
        self.highlight = None
        self.normal = None

        self.mode = BROWS # start with browsing directory
        self.edit_allowed = True
        self.note_highlight = True
        self.line_numbers = None # None or str(number_of_lines_in_buffer)

        self.file_to_open = None
        self.cwd = None # Directory(path, dirs, files)
        self.buffer = None # Buffer(path, lines)
        self.tags = None # Tags(path, data)
        self.report = None # Report(path, code_review)

        """ filters """
        self.filter_on = False
        self.filtered_files = None # Directory(path, [], files)
        self.path_filter = None
        self.content_filter = None
        self.tag_filter = None


    def set_coloring(self, highlight, normal):
        self.highlight = highlight
        self.normal = normal


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
