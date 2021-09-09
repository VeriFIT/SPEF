


class Buffer:
    def __init__(self, lines):
        self.lines = lines
        self.is_saved = True

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, index):
        return self.lines[index]

    def set_save_status(self, status):
        self.is_saved = status

    def insert(self, cursor, string):
        row, col = cursor.row, cursor.col
        current_line = self.lines.pop(row)
        new_line = current_line[:col] + string + current_line[col:]
        self.lines.insert(row, new_line)
        self.set_save_status(False)

    def delete(self, cursor):
        row, col = cursor.row, cursor.col
        if (row, col) < (len(self) - 1, len(self[row])):
            current_line = self.lines.pop(row)
            if current_line != '':
                if col < len(current_line):
                    new_line = current_line[:col] + current_line[col + 1:]
                else:
                    next_line = self.lines.pop(row)
                    new_line = current_line + next_line
                self.lines.insert(row, new_line)
            self.set_save_status(False)


    def newline(self, cursor):
        row, col = cursor.row, cursor.col
        current_line = self.lines.pop(row)
        self.lines.insert(row,current_line[:col])
        self.lines.insert(row + 1, current_line[col:])
        self.set_save_status(False)

    def tab(self, cursor):
        row, col = cursor.row, cursor.col
        current_line = self.lines.pop(row)
        new_line = current_line[:col] + '\t' + current_line[col:]
        self.lines.insert(row, new_line)
        self.set_save_status(False)

