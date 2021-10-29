from random import randint


class Config:
    def __init__(self, left_screen, right_screen):
        self.left_screen = left_screen
        self.right_screen = right_screen

        """ view window """
        self.left_win = None
        self.right_win = None

        """ screen cursor """
        self.left_cursor = None
        self.right_cursor = None

        """ coloring """
        self.highlight = None
        self.normal = None

        """ browsing """
        self.brows_dir = None # current working directory


        """ editing """
        self.file_to_open = None
        self.file_buffer = None

        self.edit_file = "None" # editing file


    def set_coloring(self, highlight, normal):
        self.highlight = highlight
        self.normal = normal


    """ BROWSING """
    def set_current_directory(self, directory):
        self.brows_dir = directory



    """ EDITING """ 
    def start_edit(self, filename):
        self.edit_file = filename

    def read_file(self):
        string = str(randint(0,100))
        self.edit_file = string

