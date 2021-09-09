

class Window:
    def __init__(self, max_rows, max_cols, row_shift=0, col_shift=0):
        self.max_rows = max_rows
        self.max_cols = max_cols

        self.row_shift = row_shift
        self.col_shift = col_shift
    
    @property
    def bottom(self):
        return self.row_shift + self.max_rows - 1

    def up(self, cursor):
        if (cursor.row == self.row_shift - 1) and (self.row_shift > 0):
            self.row_shift -= 1

    def down(self, buffer, cursor):
        if (cursor.row == self.bottom + 1) and (self.bottom < len(buffer) - 1):
            self.row_shift += 1

    def get_shifted_cursor_position(self, cursor):
        return cursor.row - self.row_shift, cursor.col - self.col_shift

    """ horizontal shift when cursor is on given left/right egde """
    def horizontal_shift(self, cursor, left_edge=5, right_edge=2):
        pages = cursor.col // (self.max_cols - right_edge)
        self.col_shift = max(pages * self.max_cols - right_edge - left_edge, 0)

