import os
import json
import yaml
import re

from utils.logger import *


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

    def __len__(self):
        return len(self.data)

    def remove_tag(self, tag_name):
        if tag_name in self.data:
            del self.data[tag_name]

    def remove_tag_by_idx(self, idx):
        i = 0
        for key in self.data:
            if i == idx:
                del self.data[key]
                return
            i+=1

    def set_tag(self, tag_name, args):
        self.data[tag_name] = [*args]

    def save_to_file(self):
        if self.data:
            with open(self.path, 'w+', encoding='utf8') as f:
                yaml.dump(self.data, f, default_flow_style=False, allow_unicode=True)

    def find(self, tag_name, args):
        if tag_name in self.data:
            return self.compare_args(self.data[tag_name], args)
        return False

    def compare_args(self, tag_args, compare_args):
        if len(compare_args) != len(tag_args):
            return False
        for i in range(len(compare_args)):
            if not re.search(str(compare_args[i]), str(tag_args[i])):
                return False
        return True

"""
code_review = { 4: { 5: ['my first note'],
                     10: ['next note on same line']},
                7: { 1: ['another line'] },
                11: { 4: ['velmi dlha', 'poznamka k voziku', 'na viac riadkov'] }}
"""
class Report:
    def __init__(self, path, code_review={}):
        self.path = path
        self.code_review = code_review # {line : { row1: ['note1'], row2: ['note2', 'note3']} }

        self.original_report = code_review.copy()
        self.last_save = code_review.copy()

        self.project_name = None
        self.login = None

    def __str__(self):
        return str(self.code_review)

    def add_note(self, row, col, text):
        if row in self.code_review:
            if col in self.code_review[row]:
                self.code_review[row][col].append(text)
            else:
                self.code_review[row][col] = [text]
        else:
            self.code_review[row] = {col: [text]}

    def delete_notes_on_line(self, row):
        if row in self.code_review:
            del self.code_review[row]

    def get_notes_on_line(self, row):
        return self.code_review[row]

    def get_next_line_with_note(self, row):
        for key in sorted(self.code_review):
            if key > row:
                return key
        return row

    def get_prev_line_with_note(self, row):
        prev_line = row
        for key in sorted(self.code_review):
            if key >= row:
                return prev_line
            prev_line = key
        return prev_line


    """ move notes to correct line after adding/removing line in buffer """
    def notes_lines_shift(self, row, col, row_shift=0, col_shift=0):
        new_code_review = self.code_review.copy()
        for y in self.code_review:
            # x shift
            shifted_notes = self.code_review[y].copy()
            for x in self.code_review[y]:
                notes = self.code_review[y][x].copy()
                if y > row or (row_shift >= 0 and y == row and x > col):
                    del shifted_notes[x]
                    new_x = int(x)+col_shift
                    if new_x in shifted_notes:
                        shifted_notes[new_x].extend(notes)
                    else:
                        shifted_notes[new_x] = notes
                if y == row and x == col:
                    del shifted_notes[x]

            # y shift
            if y > row or (row_shift >= 0 and y == row and x > col):
                del new_code_review[y]
                new_y = int(y)+row_shift
                if new_y in new_code_review:
                    new_code_review[new_y].update(shifted_notes)
                else:
                    new_code_review[new_y] = shifted_notes                    
        self.code_review = new_code_review


class UserInput:
    def __init__(self):
        self.text = []
        self.pointer = 0
        self.col_shift = 0

        self.pages = 0

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
        self.pages = self.pointer // (width - 1)
        self.col_shift = self.pages * shift

    def get_shifted_pointer(self):
        return self.pointer - self.col_shift - (1 if self.col_shift > 0 else 0)



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
            report.notes_lines_shift(row, col, col_shift=1)
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
            if len(self) < old_length:
                report.notes_lines_shift(row+1, col, -1, old_line_len)
            else:
                report.notes_lines_shift(row+1, col, 0, -1)
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
            report.notes_lines_shift(row+1, col, 1, -col)
        return report


    def tab(self, win):
        row = win.cursor.row - win.begin_y
        col = win.cursor.col - win.begin_x
        current_line = self.lines.pop(row)
        new_line = current_line[:col] + '\t' + current_line[col:]
        self.lines.insert(row, new_line)
        self.set_save_status(False)



# END