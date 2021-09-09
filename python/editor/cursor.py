from buffer import Buffer


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

    def up(self, buffer):
        if self.row > 0:
            self.row -= 1
            self._restrict_col(buffer)

    def down(self, buffer):
        if self.row < len(buffer) - 1:
            self.row += 1
            self._restrict_col(buffer)

    def left(self, buffer):
        if self.col > 0: # if not start of the line
            self.col -= 1
        elif self.row > 0: # move left outside buffer => move to the end of prev line if there is one
            self.row -= 1
            self.col = len(buffer[self.row])

    def right(self, buffer):
        if self.col < len(buffer[self.row]): # if not end of the line
            self.col += 1
        elif self.row < len(buffer) - 1: # move right outside buffer => move to the start of next line if there is one
            self.row += 1
            self.col = 0

    """ restrict the cursors col to be within the line we move to """
    def _restrict_col(self,buffer):
        self._col = min(self._col_last, len(buffer[self.row]))

