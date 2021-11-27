import curses
import os

from buffer import UserInput
from logger import *
from coloring import *

"""
    CTRL + Q    delete filter

    CTRL + L    hard reload (from original buff)
    CTRL + H    enable/disable note highlight

    CTRL + D    show notes detail
    CTRL + R    remove note
    CTRL + E    edit note
    CTRL + Down next note
    CTRL + Up   prev note

    CTRL + N    show/hide line numbers
"""


def print_hint(conf, filter_mode=False):
    screen = conf.down_screen
    screen.erase()
    screen.border(0)
    size = screen.getmaxyx()

    view_switch = "off" if conf.quick_view else "on"
    B_HELP = {"F1":"help", "F2":"menu", "F3":f"view {view_switch}","F4":"edit", "F5":"copy",
                "F6":"rename", "F8":"delete", "F9":"filter", "F10":"exit"}
    E_HELP = {"F1":"help", "F2":"save", "F3":"view/tag", "F4":"note", "F5":"goto",
                "F8":"reload", "F9":"filter", "F10":"exit"}
    V_HELP = {"F1":"help", "F4":"edit file", "F5":"goto", "F9":"filter", "F10":"exit"}
    T_HELP = {"F1":"help", "F4":"edit tags", "F9":"filter", "F10":"exit"}

    if filter_mode:
        if conf.is_brows_mode(): filter_type = "path"
        elif conf.is_view_mode(): filter_type = "content"
        elif conf.is_tag_mode(): filter_type = "tag"
        else: filter_type = None

        if not filter_type:
            help_dict = {}
        else:
            help_dict = {"F1":"help", "ESC":"exit filter mode", 
                        "F8":"remove all filters", "F9":f"edit {filter_type} filter"}
    elif conf.is_brows_mode():
        help_dict = B_HELP
    elif conf.is_view_mode():
        help_dict = E_HELP if conf.edit_allowed else V_HELP
    elif conf.is_tag_mode():
        help_dict = T_HELP
    else:
        help_dict = {}


    string = ""
    for key in help_dict:
        hint = " | " + str(key) + ":" + str(help_dict[key])
        if len(string) + len(hint) <= size[1]:
            string += hint
    screen.addstr(1, 1, string[2:])
    screen.refresh()



""" show file name/path of currently opened file/directory """
def show_path(screen, path, max_cols):
    while len(path) > max_cols-2:
        path = path.split(os.sep)[1:]
        path = "/".join(path)
    dir_name = str(path)
    screen.addstr(0, int(max_cols/2-len(dir_name)/2), dir_name)
    screen.refresh()


def show_user_input(screen, user_input, max_rows, max_cols, conf, color=None):
    # screen.move(max_rows, 1)
    # screen.clrtoeol()
    # screen.border(0)
    # screen.refresh()

    if user_input:
        user_input_str = ''.join(user_input.text)

        if user_input.col_shift > 0 and len(user_input_str) > user_input.col_shift:
            user_input_str = user_input_str[user_input.col_shift + 1:]

    if not user_input.text:
        empty_message = ""
        if conf.is_brows_mode(): empty_message = "add path filter... ex: test1/unit_*.* "
        elif conf.is_view_mode(): empty_message = "add content filter... ex: def test1 "
        elif conf.is_tag_mode(): empty_message = "add tag filter... ex: #plagiat(.*) "
        empty_message += " "*(max_cols-1-len(empty_message))
        screen.addstr(max_rows, 1, empty_message[:max_cols-1], curses.color_pair(FILTER) | curses.A_ITALIC)
    else:
        user_input_str += " "*(max_cols-1-len(user_input_str))
        screen.addstr(max_rows, 1, user_input_str[:max_cols-1], color if color else curses.color_pair(FILTER))
    screen.refresh()


def show_directory_content(screen, win, cwd, conf):
    screen.erase()
    screen.border(0)

    print_hint(conf)

    dirs, files = cwd.get_shifted_dirs_and_files(win.row_shift)
    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1
    # last_row = win.last_row
    try:
        """ show dir content """
        if cwd.is_empty():
            if conf.filter_not_empty():
                screen.addstr(1, 1, "* No file matches with current filter *", curses.A_NORMAL | curses.A_BOLD)
            else:
                screen.addstr(1, 1, "* This directory is empty *", curses.A_NORMAL | curses.A_BOLD)
        else:
            i=1
            for dir_name in dirs:
                if i > max_rows:
                    break
                elif i == max_rows and conf.filter:
                    if conf.filter.path:
                        break
                coloring = (curses.color_pair(SELECT) if i+win.row_shift == win.cursor.row+1 else curses.A_NORMAL)
                screen.addstr(i, 1, "/"+str(dir_name[:max_cols-2]), coloring | curses.A_BOLD)
                i+=1
            for file_name in files:
                if i > max_rows:
                    break
                elif i == max_rows and conf.filter:
                    if conf.filter.path:
                        break
                coloring = curses.color_pair(SELECT) if i+win.row_shift == win.cursor.row+1 else curses.A_NORMAL
                screen.addstr(i, 1, str(file_name[:max_cols-1]), coloring)
                i+=1

        """ show path filter if there is one """
        if conf.filter:
            if conf.filter.path:
                user_input = UserInput()
                user_input.text = conf.filter.path
                show_user_input(screen, user_input, max_rows, max_cols, conf)

        """ show dir name """
        show_path(screen, cwd.path, max_cols)

    except Exception as err:
        log("show directory | "+str(err))
    finally:
        screen.refresh()



def show_file_content(screen, win, buffer, report, conf, user_input=None):
    screen.erase()
    screen.border(0)

    print_hint(conf)

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1
    # last_row = win.last_row

    if buffer is None:
        screen.refresh()
        return

    """ highlight lines with notes """
    colored_lines = []
    if conf.note_highlight and report:
        for note in report.code_review:
            row, col, text = note
            colored_lines.append(row)

    shift = len(conf.line_numbers)+1 if conf.line_numbers else 0
    try:
        """ show file content """
        if buffer:
            for row, line in enumerate(buffer[win.row_shift : max_rows + win.row_shift]):
                if (user_input is not None) and (row == max_rows-1):
                    break
                if (row + win.begin_y == win.cursor.row - win.row_shift) and (win.col_shift > 0):
                    line = line[win.col_shift + 1:]
                if len(line) > max_cols - 1 - shift:
                    line = line[:max_cols - 1 - shift]
                color = curses.color_pair(NOTE_HIGHLIGHT) if (row+1+win.row_shift in colored_lines) else curses.A_NORMAL
                if conf.line_numbers:
                    screen.addstr(row+1, 1, str(row+win.row_shift), curses.color_pair(LINE_NUM))
                screen.addstr(row+1, 1+shift, line, color)

        """ show user input from note entering """
        if user_input:
            color=curses.color_pair(NOTE_MGMT)
            show_user_input(screen, user_input, max_rows, max_cols, conf, color=color)
        elif conf.filter:
            if conf.filter.content:
                user_input = UserInput()
                user_input.text = conf.filter.content
                show_user_input(screen, user_input, max_rows, max_cols, conf)

        """ show file name """
        show_path(screen, buffer.path, max_cols+(shift if conf.line_numbers else 1))

    except Exception as err:
        log("show file | "+str(err))
    finally:
        screen.refresh()



def show_tags(screen, win, tags, conf, user_input=None):
    screen.erase()
    screen.border(0)

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1
    # last_row = win.last_row
    try:
        """ show tags """
        if tags.data:
            for row, name in enumerate(tags.data):
                if row == max_rows:
                    break
                params = tags.data[name]
                str_params = "(" + ",".join(map(str,params)) + ")"
                line = "#"+str(name)+str_params
                if len(line) > max_cols -1:
                    line = line[:max_cols - 1]
                screen.addstr(row+1, 1, line)

        """ show user input with command for tag management """
        if user_input:
            color=curses.color_pair(TAG_MGMT)
            show_user_input(screen, user_input, max_rows, max_cols, conf, color=color)
        elif conf.filter:
            if conf.filter.tag:
                user_input = UserInput()
                user_input.text = conf.filter.tag
                show_user_input(screen, user_input, max_rows, max_cols, conf)

        """ show file name """
        show_path(screen, tags.path, max_cols)

    except Exception as err:
        log("show tags | "+str(err))
    finally:
        screen.refresh()
