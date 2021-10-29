
"""
-Window reprezentuje zobrazovane okno (view win) v obrazovke (screen)
-shift sluzi na zobrazenie spravnej casti obsahu do okna  

"""

class Window:
    def __init__(self, max_rows, max_cols, begin_row, begin_col):
        """ size """
        self.max_rows = max_rows # heigh
        self.max_cols = max_cols # width

        """ position shift """
        self.row_shift = 0
        self.col_shift = 0

        """ location / coordinates """
        self.begin_row = begin_row
        self.begin_col = begin_col
        self.end_row = begin_row + max_rows
        self.end_col = begin_col + max_cols

    @property
    def bottom(self):
        # return self.row_shift + self.max_rows - 1 # without borders
        return self.row_shift + self.max_rows - 1 - 2 # with borders
        # return self.row_shift + self.max_rows - 1 - 2 # with borders

    def up(self, current_row):
        if (current_row == self.row_shift - 1) and (self.row_shift > 0):
            self.row_shift -= 1

    def down(self, buffer, current_row):
        if (current_row == self.bottom + 1) and (self.bottom < len(buffer) - 1):
            self.row_shift += 1

    def get_shifted_cursor_position(self, current_row, current_col):
        return current_row - self.row_shift, current_col - self.col_shift

    """ horizontal shift when cursor is on given left/right egde """
    def horizontal_shift(self, cursor, left_edge=5, right_edge=2):
        pages = cursor.col // (self.max_cols - right_edge)
        self.col_shift = max(pages * self.max_cols - right_edge - left_edge, 0)

    def reset_shifts(self):
        self.row_shift = 0
        self.col_shift = 0

    def resize(self, max_rows, max_cols):
        self.max_rows = max_rows
        self.max_cols = max_cols

        # check for shifts (row and col)
