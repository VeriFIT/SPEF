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
        self.data = data # {"tag_name": [param1, param2], "tag_name": []}

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


""" report for current project """
# class Report:
#     def __init__(self, code_review=None):
#         """ data """
#         self.code_review = code_review # {"file": [notes], "file": [notes]}
#         self.auto_report = None # TODO
#         self.auto_notes = None # [notes]
#         self.other_notes = None # [notes]

#         """ project identification """
#         self.project_path = None


"""
poznamka nemusi mat line,col ak ide o poznamku mimo code review
napr "chybajuca dokumentacia" je poznamka nepatriaca k ziadnemu konkretnemu riadku v kode
- jedine poznamky ktore su ulozene v subore ako dict (yaml) a maju row,col su poznamky z code_review
- vsetky ostatne poznamky su ulozene v subore ako pole stringov (txt) a nemaju ziaden row,col
"""
class Note:
    def __init__(self, text, row=None, col=None):
        self.row = row
        self.col = col
        self.text = text

        # self.score = None # pridanie/odobranie bodoveho hodnotenia z celkoveho skore

    def is_typical(self, env):
        for note in env.typical_notes:
            if note.text == self.text:
                return True
        return False

    def set_as_typical(self, env):
        env.typical_notes.append(self)

    def remove_from_typical(self, env):
        for idx, note in enumerate(env.typical_notes):
            if note.text == self.text:
                del env.typical_notes[idx]



"""
report by mal byt k celemu studentskemu projektu v podadresari reports
celkovy report sa sklada zo suborov:
    * automaticke hodnotenie z automatickych testov
    * poznamky k automatickym testom
    * poznamky z code review
    * dalsie nezavisle poznamky
tieto casti su ulozene v env ako:
    * auto_report = ??? # je z nich mozne vygenerovat tagy
    * auto_notes = Report(path, data)
    * code_review = Report(path, data)
    * other_notes = Report(path, data)
-auto_report, auto_notes, other_notes sa nacitava s kazdym novym projektom
-code_review sa nacitava s kazdym novym suborom
"""

"""
code_review = { 4: { 5: ['my first note'],
                     10: ['next note on same line']},
                7: { 1: ['another line'] },
                11: { 4: ['velmi dlha', 'poznamka k voziku', 'na viac riadkov'] }}
data = {line : { row1: ['note1'], row2: ['note2', 'note3']} }
"""
class Report:
    def __init__(self, path, data=None):
        self.path = path # cesta k suboru ktory obsahuje report (typicky fileXYZ_report.yaml)
        self.data = [] if data is None else data # [notes]

        self.original_report = data.copy()
        self.last_save = data.copy()


    def __str__(self):
        return str(self.data)

    def __len__(self):
        return len(self.data)

    def add_note(self, row, col, text):
        note = Note(text, row=row, col=col)
        self.data.append(note)
        """ sort notes by col and row """
        self.data.sort(key=lambda note: note.col)
        self.data.sort(key=lambda note: note.row)

    def delete_notes_on_line(self, row):
        for idx, note in enumerate(list(self.data)):
            if note.row == row:
                del self.data[idx]


    def get_notes_on_line(self, row):
        notes = []
        for note in enumerate(self.data):
            if note.row == row:
                notes.append(note)
        return notes


    def get_next_line_with_note(self, row):
        self.data.sort(key=lambda note: note.row)
        for note in self.data:
            if note.row > row:
                return note.row
        return row

    def get_prev_line_with_note(self, row):
        prev_line = row
        self.data.sort(key=lambda note: note.row)
        for note in self.data:
            if note.row >= row:
                return prev_line
            prev_line = note.row
        return prev_line


    """ move notes to correct line after adding/removing line in buffer """
    def notes_lines_shift(self, row, col, row_shift=0, col_shift=0):
        for note in self.data:
            if (note.row>row) or (row_shift>=0 and note.row==row and note.col>col):
                note.col += col_shift
                note.row += row_shift

    def save_to_file(self):
        notes = {}
        for note in self.data:
            if note.row is not None and note.col is not None:
                if note.row in notes:
                    if note.col in notes[note.row]:
                        notes[note.row][note.col].append(note.text)
                    else:
                        notes[note.row][note.col] = [text]
                else:
                    notes[note.row] = {note.col: [text]}
            else:
                notes[0][0].append(note.text)
        with open(self.path, 'w+', encoding='utf8') as f:
            yaml.dump(notes, f, default_flow_style=False, allow_unicode=True)


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