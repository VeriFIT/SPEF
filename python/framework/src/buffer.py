import os
import json
import re

from logger import *


"""
data = {'documentation': ['ok'],
        'test0': [],
        'test1': ['5', '4', '8'],
        'test2': ['5']}
"""
class Tags:
    def __init__(self, path, data):
        self.path = path
        self.data = data

    def __str__(self):
        return str(self.data)

    def remove_tag(self, tag_name):
        if tag_name in self.data:
            del self.data[tag_name]

    def set_tag(self, tag_name, args):
        self.data[tag_name] = [*args]

    def save_to_file(self):
        if self.data:
            json_string = json.dumps(self.data, indent=4, sort_keys=True)
            with open(self.path, 'w+') as f:
                f.write(json_string)

    def find(self, tag_name, args):
        if tag_name in self.data:
            return self.compare_args(self.data[tag_name], args)
        return False

    def compare_args(self, tag_args, compare_args):
        if len(compare_args) > len(tag_args):
            return False
        for i in range(len(compare_args)):
            if not re.search(str(compare_args[i]), str(tag_args[i])):
                return False
        return True

"""
code_review = {'some_file.py': [(4, 5, 'my first note'),
                                (7, 25, 'another'),
                                (11, 93, 'poznamka k voziku')],
                'documentation.txt': [(2, 85, 'hello!')]}
"""
class Report:
    def __init__(self, path, code_review=None):
        self.path = path
        self.code_review = code_review

        self.original_report = code_review.copy()
        self.last_save = code_review.copy()

        self.project_name = None
        self.login = None

    def __str__(self):
        return str(self.code_review)

    def add_note(self, file_name, row, col, text):
        note = (row, col, text)
        if file_name in self.code_review:
            self.code_review[file_name].append(note)
        else:
            self.code_review[file_name] = [note]

    def delete_notes_on_line(self, file_name, row):
        if file_name in self.code_review:
            notes = self.code_review[file_name].copy()
            for idx, note in enumerate(self.code_review[file_name]):
                y, x, _ = note
                if y == row:
                    notes.pop(idx)
            self.code_review[file_name] = notes

    def delete_note(self, file_name, row, col):
        if file_name in self.code_review:
            notes = self.code_review[file_name].copy()
            for idx, note in enumerate(self.code_review[file_name]):
                y, x, _ = note
                if y == row and x == col:
                    notes.pop(idx)
            self.code_review[file_name] = notes

    def get_notes_on_line(self, file_name, row):
        notes = []
        if file_name in self.code_review:
            for note in self.code_review[file_name]:
                y, x, text = note
                if y == row:
                    notes.append(note)
        return notes

    def get_next_line_with_note(self, file_name, row):
        if file_name in self.code_review:
            for note in sorted(self.code_review[file_name]):
                y, x, _ = note
                if y > row:
                    return note
        return None

    def get_prev_line_with_note(self, file_name, row):
        if file_name in self.code_review:
            prev_note = None
            for note in sorted(self.code_review[file_name]):
                y, x, _ = note
                if y >= row:
                    return prev_note
                prev_note = note
        return None


    """ move notes to correct line and col after adding/removing line in buffer """
    def notes_lines_shift(self, file_name, row, col, row_shift=0, col_shift=0):
        if file_name in self.code_review:
            new_notes = []
            for note in self.code_review[file_name]:
                y, x, text = note
                if y > row or (row_shift >= 0 and y == row and x > col):
                    new_note = (y+row_shift, x+col_shift, text)
                    new_notes.append(new_note)
                elif not (y == row and x == col):
                    new_notes.append(note)
            self.code_review[file_name] = new_notes



class UserInput:
    def __init__(self):
        self.text = []
        self.pointer = 0
        self.col_shift = 0

    def __len__(self):
        return len(self.text)

    def reset(self):
        self.text = []
        self.pointer = 0
        self.col_shift = 0

    def left(self, win):
        if self.pointer > 0:
            self.pointer -= 1
        self.horizontal_shift(win)

    def right(self, win):
        if self.pointer < len(self):
            self.pointer += 1
        self.horizontal_shift(win)

    def delete_symbol(self, win):
        if self.pointer < len(self):
            del self.text[self.pointer]
            # self.text.pop(self.pointer)
        self.horizontal_shift(win)

    def insert_symbol(self, win, symbol):
        self.text.insert(self.pointer, symbol)
        self.pointer += 1
        self.horizontal_shift(win)


    def horizontal_shift(self, win):
        width = win.end_x - win.begin_x
        shift = width - 1 - 1
        pages = self.pointer // (width - 1)
        self.col_shift = pages * shift

    def get_shifted_pointer(self):
        return self.pointer - self.col_shift - (1 if self.col_shift > 0 else 0)


"""
lines = ["this is first line",
        "second line",
        "",
        "line4"]
"""
class Buffer:
    def __init__(self, path, lines):
        self.path = path
        self.lines = lines

        self.original_buff = lines.copy()
        self.last_save = lines.copy()

        self.is_saved = True

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, index):
        return self.lines[index]

    def set_save_status(self, status):
        self.is_saved = status

    def insert(self, win, string, report=None):
        row = win.cursor.row - win.begin_y
        col = win.cursor.col - win.begin_x
        if self.lines:
            current_line = self.lines.pop(row)
            new_line = current_line[:col] + string + current_line[col:]
        else:
            new_line = string
        self.lines.insert(row, new_line)
        self.set_save_status(False)
        """ shift notes """
        if report:
            file_name = os.path.basename(self.path)
            report.notes_lines_shift(file_name, row, col, col_shift=1)
        return report

    def delete(self, win, report=None):
        row = win.cursor.row - win.begin_y
        col = win.cursor.col - win.begin_x
        old_length = len(self)
        old_line_len = len(self[row])
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
        """ shift notes """
        if report:
            file_name = os.path.basename(self.path)
            if len(self) < old_length:
                report.notes_lines_shift(file_name, row+1, col, -1, old_line_len)
            else:
                report.notes_lines_shift(file_name, row+1, col, 0, -1)
            # row_shift, col_shift = -1, old_line_len if len(self) < old_length else 0, -1
            # report.notes_lines_shift(file_name, row+1, col, row_shift, col_shift)
        return report


    def newline(self, win, report=None):
        row = win.cursor.row - win.begin_y
        col = win.cursor.col - win.begin_x
        old_line_len = len(self[row])
        if self.lines:
            current_line = self.lines.pop(row)
            self.lines.insert(row, current_line[:col])
            self.lines.insert(row + 1, current_line[col:])
        else:
            self.lines.insert(row, "")
        self.set_save_status(False)
        """ shift notes """
        if report:
            file_name = os.path.basename(self.path)
            report.notes_lines_shift(file_name, row+1, col, 1, -col)
        return report


    def tab(self, win):
        row = win.cursor.row - win.begin_y
        col = win.cursor.col - win.begin_x
        current_line = self.lines.pop(row)
        new_line = current_line[:col] + '\t' + current_line[col:]
        self.lines.insert(row, new_line)
        self.set_save_status(False)

# END