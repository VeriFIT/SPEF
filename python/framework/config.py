from random import randint

""" modes """
BROWSING = 1
EDITING = 2
EXIT = -1

class Config:
    def __init__(self, left_screen, right_screen):
        self.left_screen = left_screen
        self.right_screen = right_screen

        self.mode = BROWSING # start with browsing directory

        """ view window """
        self.left_win = None
        self.right_win = None


        """ coloring """
        self.highlight = None
        self.normal = None


        """ browsing """
        self.cwd = None # current working directory


        """ editing """
        self.file_to_open = None
        self.file_buffer = None


    def set_coloring(self, highlight, normal):
        self.highlight = highlight
        self.normal = normal

    def set_browsing_mode(self):
        self.mode = BROWSING

    def set_editing_mode(self):
        self.mode = EDITING
    
    def set_exit_mode(self):
        self.mode = EXIT

    def set_mode(self, mode):
        self.mode = mode