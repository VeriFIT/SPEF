import os

from spef.controls.control import *
from spef.utils.logger import *

""" modes """
BROWS = 1
VIEW = 2
TAG = 3
NOTES = 4
LOGS = 5
EXIT = -1

""" current framework environment """


class Environment:
    def __init__(self, screens, windows, conf):
        """screens and windows"""
        self.screens = screens
        self.windows = windows

        self.win_center_pos = 2  # 1 = left, 2 = center, 3 = right
        self.win_left_edge, self.win_right_edge = 2, 2
        self.win_top_edge, self.win_bottom_edge = (
            conf["window"]["top_edge"],
            conf["window"]["bottom_edge"],
        )
        self.windows.set_edges(
            self.win_left_edge,
            self.win_right_edge,
            self.win_top_edge,
            self.win_bottom_edge,
        )
        self.windows.center.set_position(self.win_center_pos)

        """ environment """
        self.quick_view = conf["env"]["quick_view"]
        self.show_tags = conf["env"]["show_tags"]
        self.show_logs = conf["env"]["show_logs"]
        self.show_solution_info = conf["env"]["show_solution_info"]
        self.note_highlight = conf["env"]["note_highlight"]
        self.start_with_line_numbers = conf["env"]["start_with_line_numbers"]
        self.tab_size = conf["editor"]["tab_size"]

        self.show_cached_files = False  # *_tags.yaml and *_report.yaml

        """ file view/edit """
        self.file_edit_mode = True  # file edit or file management
        self.line_numbers = None  # None or str(number_of_lines_in_buffer)
        self.specific_line_highlight = None  # (line_number, color)

        """ notes """
        self.show_notes = False
        self.typical_notes = []  # [notes] all saved typical notes (from all projects)

        """ filter """
        self.filter = None  # Filter()
        self.filter_mode = False

        """ menu and user input """
        self.show_menu = False
        self.menu_mode = False
        self.user_input_mode = False

        self.file_to_open = None
        self.reload_buff = False
        self.editing_test_file = (
            False  # True while editing test (if file_to_open is TEST_FILE)
        )
        self.editing_report_template = False  # True if editing report template (if file_to_open is REPORT_TEMPLATE)

        self.mode = BROWS
        self.cwd = None  # Directory(path, dirs, files)
        self.buffer = None  # Buffer(path, lines)
        self.tags = None  # Tags(path, data)
        self.report = None  # Report(path, data)

        self.user_logs = []  # [("date", "type", "message"),...]
        self.user_logs_printed = []  # [("date", "type", "message"),...]
        self.user_logs_printed_shift = 0

        self.control = Control()
        self.bash_active = False
        self.bash_action = None
        self.bash_fd = None

    def set_user_control(self, contr):
        self.control.set_file_functions(contr)
        self.control.set_brows_functions(contr)
        self.control.set_tags_functions(contr)
        self.control.set_notes_functions(contr)
        self.control.set_filter_functions(contr)
        self.control.set_menu_functions(contr)
        self.control.set_user_input_functions(contr)
        self.control.set_user_logs_functions(contr)
        self.control.set_hints(self)

    def set_file_to_open(self, file_to_open, is_test_file=False):
        if self.file_to_open != file_to_open:
            self.file_to_open = file_to_open
            self.editing_test_file = is_test_file
            if self.show_tags:
                self.windows.view_up.reset()
            else:
                self.windows.view.reset()
            self.windows.tag.reset(0, 0)
            self.windows.notes.reset(0, 0)
            self.report = None

    def get_screen_for_current_mode(self):
        if self.is_brows_mode():
            if self.show_logs:
                return self.screens.left_up, self.windows.brows_up
            else:
                return self.screens.left, self.windows.brows
        if self.is_view_mode():
            if self.show_tags:
                return self.screens.right_up, self.windows.view_up
            else:
                return self.screens.right, self.windows.view
        if self.is_tag_mode():
            return self.screens.right_down, self.windows.tag
        if self.is_notes_mode():
            return self.screens.left, self.windows.notes
        if self.is_logs_mode():
            return self.screens.left_down, self.windows.logs

    def update_win_for_current_mode(self, win):
        if self.is_brows_mode():
            if self.show_logs:
                self.windows.brows_up = win
            else:
                self.windows.brows = win
        if self.is_view_mode():
            if self.show_tags:
                self.windows.view_up = win
            else:
                self.windows.view = win
        if self.is_tag_mode():
            self.windows.tag = win
        if self.is_notes_mode():
            self.windows.notes = win
        if self.is_logs_mode():
            self.windows.logs = win

    def update_center_win(self, win):
        self.windows.center = win

    def get_center_win(self, reset=False, row=None, col=None):
        if reset:
            self.windows.center.set_position(
                self.win_center_pos, screen=self.screens.center
            )
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
            self.windows.brows_up.reset(0, 0)
            self.windows.brows.reset(0, 0)

    def reset_brows_wins(self):
        self.windows.brows_up.reset(0, 0)
        self.windows.brows.reset(0, 0)

    def get_typical_notes_dict(self):
        options = {}
        if len(self.typical_notes) > 0:
            for idx, note in enumerate(self.typical_notes):
                if idx + 1 > 35:
                    break
                # 1-9 or A-Z (chr(10+55)='A')
                key = idx + 1 if idx < 9 else chr(idx + 1 + 55)
                options[str(key)] = note.text
        return options

    def get_supported_test_functions(self, bash_file):
        options = {}
        try:
            fce_str = os.popen(f"{bash_file} get_fce 2>/dev/null").read().strip()
            for item in fce_str.splitlines():
                fce, descr = item.split("=")
                fce, descr = fce.strip(), descr.strip()
                options[str(fce)] = str(descr)
            return options
        except Exception as err:
            log("get supported test functions | " + str(err))
            return {}

    """ update data """

    def update_browsing_data(self, win, cwd):
        if self.show_logs:
            self.windows.brows_up = win
        else:
            self.windows.brows = win
        self.cwd = cwd

    def update_viewing_data(self, win, buffer, report=None):
        if self.show_tags:
            self.windows.view_up = win
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
        self.show_notes = True

    def disable_note_management(self):
        self.show_notes = False

    """ line numbers """

    def enable_line_numbers(self, buffer):
        self.line_numbers = str(len(buffer))
        self.update_line_numbers_shift()

    def disable_line_numbers(self):
        self.line_numbers = None
        self.update_line_numbers_shift()

    def update_line_numbers_shift(self):
        shift = 1 if self.line_numbers is None else len(self.line_numbers) + 1
        self.windows.view_up.set_line_num_shift(shift)
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

    def set_logs_mode(self):
        self.mode = LOGS

    def set_exit_mode(self):
        self.mode = EXIT

    """ cycling between modes """

    def switch_to_next_mode(self):
        if self.is_brows_mode():
            self.mode = VIEW  # Brows -> View
        elif self.is_view_mode():
            if self.show_tags:
                self.mode = TAG  # View -> Tag
            else:
                if self.show_notes:
                    self.mode = NOTES  # View -> Notes
                else:
                    if self.show_logs:
                        self.mode = LOGS  # View -> Logs
                    else:
                        self.mode = BROWS  # View -> Brows
        elif self.is_tag_mode():
            if self.show_notes:
                self.mode = NOTES  # Tag -> Notes
            else:
                if self.show_logs:
                    self.mode = LOGS  # Tags -> Logs
                else:
                    self.mode = BROWS  # Tag -> Brows
        elif self.is_notes_mode():
            self.mode = VIEW  # Notes -> View
        elif self.is_logs_mode():
            self.mode = BROWS  # Logs -> Brows

    """ check mode """

    def is_brows_mode(self):
        return self.mode == BROWS

    def is_view_mode(self):
        return self.mode == VIEW

    def is_tag_mode(self):
        return self.mode == TAG

    def is_notes_mode(self):
        return self.mode == NOTES

    def is_logs_mode(self):
        return self.mode == LOGS

    def is_exit_mode(self):
        return self.mode == EXIT

    def is_filter_mode(self):
        return self.filter_mode

    def is_menu_mode(self):
        return self.menu_mode

    def is_user_input_mode(self):
        return self.user_input_mode
