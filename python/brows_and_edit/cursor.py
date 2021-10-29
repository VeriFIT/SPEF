
"""
-Cursor reprezentuje kurzor ci uz v ramci adresarovej struktury (pre vyber)
alebo v ramci otvoreneho suboru (pre zobrazovanie alebo upravu suboru)

"""

class Cursor:
    def __init__(self, row=0, col=0, col_last=None):
        self.row = row
        self._col = col
        self._col_last = col_last if col_last else col


    @property
    def col(self):
        return self._col
    
    @col.setter
    def col(self,col):
        self._col = col
        self._col_last = col

    def up(self, buffer, win, use_restrictions=True):
        if self.row > win.begin_row: # (if row > 0)
            self.row -= 1
            if use_restrictions:
                self._restrict_col(buffer, win)

    def down(self, buffer, win, use_restrictions=True):
        # if self.row < len(buffer) - 1:
        if self.row < len(buffer) - 1 + win.begin_row:
            self.row += 1
            if use_restrictions:
                self._restrict_col(buffer, win)

    def left(self, buffer, win):
        if self.col > win.begin_col: # if not start of the line (if col > 0)
            self.col -= 1
        elif self.row > win.begin_row: # (if row > 0) move to the end of prev line if there is one
            self.row -= 1
            # self.col = len(buffer[self.row])
            self.col = len(buffer[self.row]) + win.begin_col

    def right(self, buffer, win):
        # if self.col < len(buffer[self.row]): # if not end of the line
        if self.col < len(buffer[self.row]) + win.begin_col: # if not end of the line
            self.col += 1
        # elif self.row < len(buffer) - 1: # move to the start of next line if there is one
        elif self.row < len(buffer) - 1 + win.begin_row: # move to the start of next line if there is one
            self.row += 1
            self.col = win.begin_col # col = 0

    """ restrict the cursors column to be within the line we move to """
    def _restrict_col(self, buffer, win):
        self._col = min(self._col_last, len(buffer[self.row]+win.begin_col))

