import curses
import os

from logger import *


# browsing
B_HELP = {"F1":"help", "F2":"menu", "F3":"view/tag",
            "F4":"edit", "F5":"copy", "F6":"rename",
            "F8":"delete", "F9":"filter", "F10":"exit"}

# editing = is_view_mode + edit_allowed
E_HELP = {"F1":"help", "F2":"save", "F3":"view/tag",
            "F4":"note", "F5":"goto", "F8":"reload",
            "F9":"filter", "F10":"exit"}

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

# viewing = is_view_mode + not edit_allowed
V_HELP = {"F1":"help", "F4":"edit", "F5":"goto",
            "F9":"filter", "F10":"exit"}

# tagging
T_HELP = {"F1":"help", "F4":"edit",
            "F9":"filter", "F10":"exit"}


# browsing with filter on
F_B_HELP = {"F1":"help", "ESC":"exit filter mode", "F8":"clear filter", "F9":"edit path filter"}
# viewing with filter on
F_V_HELP = {"F1":"help", "ESC":"exit filter mode", "F8":"clear filter", "F9":"edit content filter"}
# tagging with filter on
F_T_HELP = {"F1":"help", "ESC":"exit filter mode", "F8":"clear filter", "F9":"edit tag filter"}


def print_hint(conf):
    screen = conf.down_screen
    screen.erase()
    screen.border(0)
    size = screen.getmaxyx()

    if conf.filter_on:
        if conf.is_brows_mode():
            help_dict = F_B_HELP
        elif conf.is_view_mode():
            help_dict = F_V_HELP
        elif conf.is_tag_mode():
            help_dict = F_T_HELP
        else:
            help_dict = {}
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



def show_directory_content(screen, win, cwd, conf, user_input=None):
    screen.erase()
    screen.border(0)

    print_hint(conf)

    if conf.filter_on and conf.filtered_files is not None:
        cwd = conf.filtered_files

    dirs, files = cwd.get_shifted_dirs_and_files(win.row_shift)


    max_cols = win.end_x - win.begin_x
    last_row = win.end_y - win.begin_y - 1
    try:
        """ show dir name """
        show_path(screen, cwd.path, max_cols)

        """ show dir content """
        if cwd.is_empty():
            if conf.filter_on:
                screen.addstr(1, 1, "* No file matches with current filter *", conf.normal | curses.A_BOLD)
            else:
                screen.addstr(1, 1, "* This directory is empty *", conf.normal | curses.A_BOLD)
        else:
            i=1
            for dir_name in dirs:
                # if i > win.end_y - 1:
                if (i > win.end_y - 1) or ((user_input is not None or conf.path_filter) and i == last_row):
                    break
                coloring = (conf.highlight if i+win.row_shift == win.cursor.row+1 else conf.normal)
                screen.addstr(i, 1, "/"+str(dir_name[:max_cols-2]), coloring | curses.A_BOLD)
                i+=1
            for file_name in files:
                # if i > win.end_y - 1:
                if (i > win.end_y - 1) or ((user_input is not None or conf.path_filter) and i == last_row):
                    break
                coloring = conf.highlight if i+win.row_shift == win.cursor.row+1 else conf.normal
                screen.addstr(i, 1, str(file_name[:max_cols-1]), coloring)
                i+=1

        """ show user input for path filter or show path filter if there is one """
        if user_input:
            user_input_str = ''.join(user_input.text)
            if user_input.col_shift > 0:
                user_input_str = user_input_str[user_input.col_shift + 1:]
            if len(user_input_str) > max_cols:
                user_input_str = user_input_str[:max_cols - 1]
            screen.addstr(last_row, 1, user_input_str)
        elif conf.path_filter:
            user_input_str = conf.path_filter
            if len(user_input_str) > max_cols:
                user_input_str = user_input_str[:max_cols - 1]
            screen.addstr(last_row, 1, user_input_str)

    except Exception as err:
        log("show directory | "+str(err))
    finally:
        screen.refresh()



def show_file_content(screen, win, buffer, report, conf, user_input=None):
    screen.erase()
    screen.border(0)

    print_hint(conf)

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y
    last_row = win.end_y - win.begin_y - 1

    if buffer is None:
        screen.refresh()
        return

    """ highlight lines with notes """
    colored_lines = []
    if conf.note_highlight and report:
        file_name = os.path.basename(buffer.path)
        if file_name in report.code_review:
            notes = report.code_review[file_name]
            for note in notes:
                row, col, text = note
                colored_lines.append(row)

    shift = len(conf.line_numbers)+1 if conf.line_numbers else 0
    try:
        """ show file name """
        show_path(screen, buffer.path, max_cols+(shift if conf.line_numbers else 1))

        """ show file content """
        if buffer:
            for row, line in enumerate(buffer[win.row_shift : max_rows + win.row_shift - 1]):
                if (user_input is not None) and (row == last_row-1):
                    break
                if (row + win.begin_y == win.cursor.row - win.row_shift) and (win.col_shift > 0):
                    line = line[win.col_shift + 1:]
                if len(line) > max_cols - shift:
                    line = line[:max_cols - 1 - shift]
                color = conf.highlight if (row+1+win.row_shift in colored_lines) else conf.normal
                if conf.line_numbers:
                    screen.addstr(row+1, 1, str(row+win.row_shift), conf.normal)
                screen.addstr(row+1, 1+shift, line, color)

        """ show user input from note entering """
        if user_input:
            user_input_str = ''.join(user_input.text)
            if user_input.col_shift > 0:
                user_input_str = user_input_str[user_input.col_shift + 1:]
            if len(user_input_str) > max_cols - shift:
                user_input_str = user_input_str[:max_cols - 1 - shift]
            screen.addstr(last_row, 1+shift, user_input_str)

    except Exception as err:
        log("show file | "+str(err))
    finally:
        screen.refresh()



def show_tags(screen, win, tags, user_input=None):
    screen.erase()
    screen.border(0)

    max_cols = win.end_x - win.begin_x
    last_row = win.end_y - win.begin_y - 1
    try:
        """ show file name """
        show_path(screen, tags.path, max_cols)

        """ show tags """
        if tags.data:
            for row, name in enumerate(tags.data):
                if row == last_row-1:
                    break
                params = tags.data[name]
                str_params = "(" + ",".join(map(str,params)) + ")"
                line = "#"+str(name)+str_params
                if len(line) > max_cols:
                    line = line[:max_cols - 1]
                screen.addstr(row+1, 1, line)

        """ show user input with command for tag management """
        if user_input:
            user_input_str = ''.join(user_input.text)
            if user_input.col_shift > 0:
                user_input_str = user_input_str[user_input.col_shift + 1:]
            if len(user_input_str) > max_cols:
                user_input_str = user_input_str[:max_cols - 1]
            screen.addstr(last_row, 1, user_input_str)

    except Exception as err:
        log("show tags | "+str(err))
    finally:
        screen.refresh()
