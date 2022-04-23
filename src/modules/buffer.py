import os
import json
import yaml
import re

from utils.logger import *


class UserInput:
    def __init__(self):
        self.text = []

        self.pointer = 0
        self.col_shift = 0
        self.row_shift = 0

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

    # def up(self, win):
        # self.row_shift -= 1

    # def down(self, win):
        # self.row_shift += 1

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

    def process_to_lines(self, max_cols):
        user_input_str = ''.join(self.text)
        words = re.split(r'(\S+)', user_input_str) # split string into list of words and spaces
        split_words = []
        for word in words:
            # if any single word is longer than window, split it (otherwise it would never be printed)
            if len(word) >= max_cols:
                while len(word) >= max_cols:
                    part = word[:max_cols-1]
                    split_words.append(part)
                    word = word[max_cols-1:]
            split_words.append(word)

        lines = []
        words = split_words
        while words:
            line = ""
            word = words[0] # get first word
            while len(line)+len(word) < max_cols: # check if the word fits in the line
                """ add word to the line """
                line += word
                del words[0]
                if not words:
                    break
                word = words[0] # get next word
            lines.append(line)

        return lines


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
        if len(self.lines)>0:
            current_line = self.lines.pop(row)
            self.lines.insert(row, current_line[:col])
            self.lines.insert(row + 1, current_line[col:])
        else:
            self.lines.append("")
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

