import yaml

from spef.utils.logger import *


class Note:
    def __init__(self, text, row=None, col=None):
        self.row = row
        self.col = col
        self.text = text

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


class Report:
    def __init__(self, path, data=None):
        self.path = path # ex: fileXYZ_report.yaml
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
                        notes[note.row][note.col] = [note.text]
                else:
                    notes[note.row] = {note.col: [note.text]}
            else:
                notes[0][0].append(note.text)
        with open(self.path, 'w+', encoding='utf8') as f:
            yaml.dump(notes, f, default_flow_style=False, allow_unicode=True)
