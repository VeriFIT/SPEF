import datetime

LOG_FILE = "/home/naty/Others/ncurses/python/framework/log"

def log(message):
    day = datetime.date.today()
    time = datetime.datetime.now().strftime("%X")
    with open(LOG_FILE, 'a') as f:
        f.write("{} {} | {}\n".format(day,time,message))

class Report:
    def __init__(self, project_name, login):
        self.project_name = project_name
        self.login = login

        self.notes = None


class Buffer:
    def __init__(self, file_name, lines):
        self.file_name = file_name
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

    def insert(self, win, string):
        row = win.cursor.row - win.begin_y
        col = win.cursor.col - win.begin_x
        current_line = self.lines.pop(row)
        new_line = current_line[:col] + string + current_line[col:]
        self.lines.insert(row, new_line)
        self.set_save_status(False)

    def delete(self, win):
        row = win.cursor.row - win.begin_y
        col = win.cursor.col - win.begin_x
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


    def newline(self, win):
        row = win.cursor.row - win.begin_y
        col = win.cursor.col - win.begin_x
        current_line = self.lines.pop(row)
        self.lines.insert(row,current_line[:col])
        self.lines.insert(row + 1, current_line[col:])
        self.set_save_status(False)

    def tab(self, win):
        row = win.cursor.row - win.begin_y
        col = win.cursor.col - win.begin_x
        current_line = self.lines.pop(row)
        new_line = current_line[:col] + '\t' + current_line[col:]
        self.lines.insert(row, new_line)
        self.set_save_status(False)

# END