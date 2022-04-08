import os
import yaml

from controls.control import *
from utils.logger import *

""" modes """
BROWS = 1
VIEW = 2
TAG = 3
NOTES = 4
EXIT = -1


""" current framework environment """
class Environment:
    def __init__(self, screens, windows, conf):

        """ screens and windows """
        self.screens = screens
        self.windows = windows

        self.win_center_pos = conf['window']['position']
        self.win_left_edge, self.win_right_edge = conf['window']['left_edge'], conf['window']['right_edge']
        self.win_top_edge, self.win_bottom_edge = conf['window']['top_edge'], conf['window']['bottom_edge']
        self.windows.set_edges(self.win_left_edge, self.win_right_edge, self.win_top_edge, self.win_bottom_edge)
        self.windows.center.set_position(self.win_center_pos)


        """ environment """
        self.mode = conf['env']['mode']
        self.quick_view = conf['env']['quick_view']
        self.show_tags = conf['env']['show_tags']
        self.note_highlight = conf['env']['note_highlight']
        self.show_cached_files = conf['env']['show_cached_files'] # *_tags.yaml and *_report.yaml
        self.start_with_line_numbers = conf['env']['start_with_line_numbers']

        self.tab_size = conf['editor']['tab_size']

        """ file view/edit """
        self.file_edit_mode = True # file edit or file management
        self.line_numbers = None # None or str(number_of_lines_in_buffer)
        self.specific_line_highlight = None # (line_number, color)

        """ notes """
        self.note_management = False
        self.typical_notes = [] # [notes] all saved typical notes (from all projects)

        """ filter """
        self.filter = None # Filter()
        self.filter_mode = False

        """ menu and user input """
        self.show_menu = False
        self.menu_mode = False
        self.user_input_mode = False

        self.file_to_open = None
        self.cwd = None # Directory(path, dirs, files)
        self.buffer = None # Buffer(path, lines)
        self.tags = None # Tags(path, data)
        self.report = None # Report(path, data)

        self.control = Control()


    def set_user_control(self, contr):
        self.control.set_file_functions(contr)
        self.control.set_brows_functions(contr)
        self.control.set_tags_functions(contr)
        self.control.set_notes_functions(contr)
        self.control.set_filter_functions(contr)
        self.control.set_menu_functions(contr)
        self.control.set_user_input_functions(contr)


    def set_file_to_open(self, file_to_open):
        if self.file_to_open != file_to_open:
            self.file_to_open = file_to_open
            if self.show_tags:
                self.windows.edit.reset()
            else:
                self.windows.view.reset()
            self.windows.tag.reset(0,0)
            self.windows.notes.reset(0,0)
            self.report = None

    def get_screen_for_current_mode(self):
        if self.is_brows_mode():
            return self.screens.left, self.windows.brows
        if self.is_view_mode():
            if self.show_tags:
                return self.screens.right, self.windows.edit
            else:
                return self.screens.right_up, self.windows.view
        if self.is_tag_mode():
            return self.screens.right_down, self.windows.tag
        if self.is_notes_mode():
            return self.screens.left, self.windows.notes


    def update_win_for_current_mode(self, win):
        if self.is_brows_mode():
            self.windows.brows = win
        if self.is_view_mode():
            if self.show_tags:
                self.windows.edit = win
            else:
                self.windows.view = win
        if self.is_tag_mode():
            self.windows.tag = win
        if self.is_notes_mode():
            self.windows.notes = win

    def update_center_win(self, win):
        self.windows.center = win


    def get_center_win(self, reset=False, row=None, col=None):
        if reset:
            self.windows.center.set_position(self.win_center_pos, screen=self.screens.center)
            self.windows.center.reset(row=row, col=col)
            self.windows.center.set_border(1)
        return self.screens.center, self.windows.center


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
    
    def prepare_browsing_after_filter(self):
        if not self.is_exit_mode():
            self.set_brows_mode()
            self.disable_note_management()
            self.quick_view = True
            self.windows.brows.reset(0,0)

    def get_typical_notes_dict(self):
        options = {}
        if len(self.typical_notes) > 0:
            for idx, note in enumerate(self.typical_notes):
                if idx+1 > 35:
                    break
                key = idx+1 if idx < 9 else chr(idx+1+55) # 1-9 or A-Z (chr(10+55)='A')
                options[str(key)] = note.text
        return options

    """ update data """
    def update_browsing_data(self, win, cwd):
        self.windows.brows = win
        self.cwd = cwd

    def update_viewing_data(self, win, buffer, report=None):
        if self.show_tags:
            self.windows.edit = win
        else:
            self.windows.view = win
        self.buffer = buffer
        if report:
            self.report = report

    def update_tagging_data(self, win, tags):
        self.windows.tag = win
        self.tags = tags

    def update_report_data(self, win, report):
        self.windows.notes = win
        self.report = report


    """ file management """
    def change_to_file_edit_mode(self):
        self.file_edit_mode = True

    def change_to_file_management(self):
        self.file_edit_mode = False


    """ note management """
    def enable_note_management(self):
        self.note_management = True

    def disable_note_management(self):
        self.note_management = False


    """ line numbers """
    def enable_line_numbers(self, buffer):
        self.line_numbers = str(len(buffer))
        self.update_line_numbers_shift()

    def disable_line_numbers(self):
        self.line_numbers = None
        self.update_line_numbers_shift()

    def update_line_numbers_shift(self):
        shift = 1 if self.line_numbers is None else len(self.line_numbers)+1
        self.windows.edit.set_line_num_shift(shift)
        self.windows.view.set_line_num_shift(shift)


    """ set mode """
    def set_brows_mode(self):
        self.mode = BROWS

    def set_view_mode(self):
        self.mode = VIEW

    def set_tag_mode(self):
        self.mode = TAG

    def set_notes_mode(self):
        self.mode = NOTES

    def set_exit_mode(self):
        self.mode = EXIT

    """ cycling between modes """
    def switch_to_next_mode(self):
        if self.is_brows_mode():
            self.mode = VIEW # Brows -> View
        elif self.is_view_mode():
            if self.show_tags:
                if self.note_management:
                    self.mode = NOTES # View -> Notes
                else:
                    self.mode = BROWS # View -> Brows
            else:
                self.mode = TAG # View -> Tag
        elif self.is_tag_mode():
            if self.note_management:
                self.mode = NOTES # Tag -> Notes
            else:
                self.mode = BROWS # Tag -> Brows
        elif self.is_notes_mode():
            self.mode = VIEW # Notes -> View


    """ check mode """
    def is_brows_mode(self):
        return self.mode == BROWS

    def is_view_mode(self):
        return self.mode == VIEW

    def is_tag_mode(self):
        return self.mode == TAG

    def is_notes_mode(self):
        return self.mode == NOTES

    def is_exit_mode(self):
        return self.mode == EXIT

    def is_filter_mode(self):
        return self.filter_mode

    def is_menu_mode(self):
        return self.menu_mode

    def is_user_input_mode(self):
        return self.user_input_mode
