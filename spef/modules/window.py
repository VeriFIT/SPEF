import traceback

from spef.utils.logger import *


""" curses screens (each with its specific size and position on the main screen) """


class Screens:
    def __init__(
        self, left, right, down, center, right_up, right_down, left_up, left_down
    ):
        self.left = left
        self.right = right
        self.down = down  # for hint
        self.center = center
        self.right_up = right_up
        self.right_down = right_down
        self.left_up = left_up
        self.left_down = left_down


"""
* each window has its specific dimensions and position corresponding to the needs of its use
* multiple windows can be printed in the same screen (ex: brows and notes uses screen left)
* each window has its own cursor and other parameters (see Window object below)
* 'center' window is the only one which is used for multiple purposes (must be reset for each use)
"""


class Windows:
    def __init__(self, brows, brows_up, logs, view, view_up, tag, notes, center):
        self.brows = brows
        self.brows_up = brows_up
        self.logs = logs
        self.view = view
        self.view_up = view_up
        self.tag = tag
        self.notes = notes
        self.center = center

    def set_win_for_notes(self, win):
        self.notes = win

    def set_edges(self, left, right, top, bottom):
        self.brows.set_edges(left, right, top, bottom)
        self.center.set_edges(left, right, top, bottom)
        self.view.set_edges(left, right, top, bottom)
        self.view_up.set_edges(left, right, top, bottom)
        self.tag.set_edges(left, right, top, bottom)
        self.notes.set_edges(left, right, top, bottom)


class Cursor:
    def __init__(self, row=0, col=0, col_last=None):
        self.row = row
        self._col = col
        self._col_last = col_last if col_last else col

    @property
    def col(self):
        return self._col

    @col.setter
    def col(self, col):
        self._col = col
        self._col_last = col

    def up(self, buffer, win, use_restrictions=True):
        if self.row > 0 + win.border:
            self.row -= 1
            if use_restrictions:
                self._restrict_col(buffer, win)

    def down(self, buffer, win, use_restrictions=True):
        if self.row < len(buffer) - 1 + win.border:
            self.row += 1
            if use_restrictions:
                self._restrict_col(buffer, win)

    def left(self, buffer, win):
        if len(buffer) > 0:
            if self.col > win.begin_x:
                # if not start of the line (if col > 0)
                self.col -= 1
            elif self.row > win.begin_y:
                # (if row > 0) move to the end of prev line if there is one
                self.row -= 1
                self.col = len(buffer[self.row - win.begin_y]) + win.begin_x

    def right(self, buffer, win):
        if len(buffer) > 0:
            if self.col < len(buffer[self.row - win.begin_y]) + win.begin_x:
                # if its not end of the line
                self.col += 1
            elif self.row < len(buffer) - 1 + win.border:
                # else go to the start of next line if there is one
                self.row += 1
                self.col = win.begin_x

    """ restrict the cursors column to be within the line we move to """

    def _restrict_col(self, buffer, win):
        end_of_line = len(buffer[self.row - win.begin_y]) + win.begin_x
        self._col = min(self._col_last, end_of_line)


class Window:
    def __init__(self, height, width, begin_y, begin_x, border=0, line_num_shift=0):
        """location"""
        self._begin_x = begin_x  # width (max_cols = end_x - begin_x)
        self._begin_y = begin_y  # height (max_rows = end_y - begin_y)
        self._end_x = max(begin_x + width - 1, 0)
        self._end_y = max(begin_y + height - 1, 0)

        self.width = width
        self.height = height

        self.border = border
        self.line_num_shift = line_num_shift

        """ relative position - for center window """
        self.left_position_x = 0
        self.center_position_x = int((self.end_x - self.begin_x + 1) / 2)
        self.right_position_x = self.end_x - self.begin_x + 1
        self.position = (
            2  # for center window (position left (1), middle (2), right (3))
        )

        """ shift position """
        self.row_shift = 0  # y
        self.col_shift = 0  # x

        """ cursor """
        self.cursor = Cursor(self.begin_y, self.begin_x)  # for working with buffer
        self.tab_shift = 0  # used only in file view/edit
        self.shifted_col = self.cursor.col

        """ edges - default values """
        self.left_edge = 2
        self.right_edge = 2
        self.top_edge = 1
        self.bottom_edge = (
            1  # ak chces posuvat okno az ked je kurzor na poslednom riadku, nastav na 0
        )

    @property
    def begin_x(self):
        return self._begin_x + self.border

    @property
    def begin_y(self):
        return self._begin_y + self.border

    @property
    def end_x(self):
        return self._end_x + self.border

    @property
    def end_y(self):
        return self._end_y + self.border

    @property
    def bottom(self):
        return self.end_y + self.row_shift - 1

    @property
    def last_row(self):
        return self.end_y - self.border - 1

    def set_edges(self, left, right, top, bottom):
        self.left_edge = left
        self.right_edge = right
        self.top_edge = top
        self.bottom_edge = bottom

    def set_border(self, border):
        self.border = border

    def up(self, buffer, use_restrictions=True):
        self.cursor.up(buffer, self, use_restrictions)

        """ window shift """
        self.horizontal_shift()
        if (self.cursor.row == self.border + self.top_edge + self.row_shift - 1) and (
            self.row_shift > 0
        ):
            self.row_shift -= 1
        elif (self.cursor.row == self.border + self.row_shift - 1) and (
            self.row_shift > 0
        ):
            self.row_shift -= 1

    def down(self, buffer, filter_on=False, use_restrictions=True):
        self.cursor.down(buffer, self, use_restrictions)

        """ window shift """
        self.horizontal_shift()
        bottom = (
            self.height
            - 2
            - self.bottom_edge
            - (1 if filter_on else 0)
            + self.border
            + self.row_shift
        )
        if (self.cursor.row == bottom) and (
            self.cursor.row - self.begin_y + self.bottom_edge < len(buffer)
        ):
            self.row_shift += 1
        elif (self.cursor.row == bottom + self.bottom_edge) and (
            self.cursor.row - self.begin_y < len(buffer)
        ):
            self.row_shift += 1

    def left(self, buffer):
        old_row = self.cursor.row
        self.cursor.left(buffer, self)

        """ window shift """
        self.horizontal_shift()
        if (
            (self.cursor.row == self.row_shift + self.top_edge)
            and (self.row_shift > 0)
            and (self.cursor.row < old_row)
        ):
            self.row_shift -= 1
        elif (
            (self.cursor.row == self.row_shift)
            and (self.row_shift > 0)
            and (self.cursor.row < old_row)
        ):
            self.row_shift -= 1

        # _, col = self.get_cursor_position()
        # shift = self.end_x - self.begin_x - RIGHT_EDGE - LEFT_EDGE
        # if (col + 1 - LEFT_EDGE == self.begin_x) and (self.col_shift >= shift):
        # self.col_shift -= shift

    def right(self, buffer, filter_on=False):
        old_row = self.cursor.row
        self.cursor.right(buffer, self)

        """ window shift """
        self.horizontal_shift()
        bottom = (
            self.height
            - 2
            - self.bottom_edge
            - (1 if filter_on else 0)
            + self.border
            + self.row_shift
        )
        if (
            (self.cursor.row == bottom)
            and (self.cursor.row - self.begin_y + self.bottom_edge < len(buffer))
            and (self.cursor.row > old_row)
        ):
            self.row_shift += 1
        elif (
            (self.cursor.row == bottom + self.bottom_edge)
            and (self.cursor.row - self.begin_y < len(buffer))
            and (self.cursor.row > old_row)
        ):
            self.row_shift += 1

        # _, col = self.get_cursor_position()
        # width = self.end_x - self.begin_x
        # if ((col - self.begin_x) // (width - RIGHT_EDGE)) > 0:
        # self.col_shift += width - RIGHT_EDGE - LEFT_EDGE

    def horizontal_shift(self):
        width = self.end_x - self.begin_x
        shift = width - self.right_edge - self.left_edge
        pages = (self.cursor.col - self.begin_x) // (width - self.right_edge)
        self.col_shift = pages * shift

    def vertical_shift(self):
        shift = self.end_y - self.begin_y
        pages = (self.cursor.row - self.begin_y) // (shift)
        self.row_shift = pages * shift

    def calculate_tab_shift(self, buffer, tab_size):
        row = self.cursor.row - self.begin_y
        col = self.cursor.col - self.begin_x

        if len(buffer) > row:
            current_line = buffer.lines[row]
            tab_count = current_line.count("\t", 0, col)
            self.tab_shift = (
                tab_size - 1
            ) * tab_count  # -1 cursor shift (right/left) correction

    def get_cursor_position(self):
        # new_col = self.cursor.col - self.col_shift - (pages*(self.right_edge+self.left_edge)) - (1 if self.col_shift > 0 else 0)
        new_col = self.cursor.col - self.col_shift - (1 if self.col_shift > 0 else 0)
        new_row = self.cursor.row - self.row_shift
        return new_row, new_col + self.tab_shift

    def set_cursor(self, begin_y, begin_x):
        self.cursor = Cursor(row=begin_y, col=begin_x)

    def set_line_num_shift(self, shift):
        if self.line_num_shift != shift:
            self._begin_x = self._begin_x - self.line_num_shift + shift
            self.cursor.col = self.cursor.col - self.line_num_shift + shift
            self.line_num_shift = shift

    def set_position(self, pos, screen=None):
        self.position = pos
        if pos == 1:
            position_x = self.left_position_x
        elif pos == 2:
            position_x = self.center_position_x
        else:
            position_x = self.right_position_x
        width = self.end_x - self.begin_x + 1
        self._begin_x = position_x
        self._end_x = position_x + width - 1
        self.center_position_x = int((self.end_x - self.begin_x + 1) / 2)
        self.right_position_x = self.end_x - self.begin_x + 1
        self.reset()
        try:
            if screen:
                screen.mvwin(self.begin_y - self.border, position_x)
        except Exception as err:
            log("win set position | " + str(err) + " | " + str(traceback.format_exc()))

    def reset_shifts(self):
        self.row_shift = 0
        self.col_shift = 0

    def reset(self, row=None, col=None):
        self.reset_shifts()
        if (row != None) and (col != None):
            self.set_cursor(row, col)
        else:
            self.set_cursor(self.begin_y, self.begin_x)
