
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
        self.edit_allowed = False

        self.cwd = None # current working directory
        self.file_to_open = None
        self.file_buffer = None
        self.file_tags = None


    def set_coloring(self, highlight, normal):
        self.highlight = highlight
        self.normal = normal

    def enable_file_edit(self):
        self.edit_allowed = True

    def disable_file_edit(self):
        self.edit_allowed = False


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
