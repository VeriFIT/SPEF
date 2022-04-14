import os
import json
import yaml
import re

from utils.logger import *


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
        self.orig_file_name = None

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
