import curses
import os
import re

from modules.buffer import UserInput
from modules.directory import Directory

from utils.loading import save_buffer
from utils.coloring import *
from utils.logger import *

ESC = 27


EXIT_WITHOUT_SAVING = """WARNING: Exit without saving.\n\
    Press F2 to save and exit.\n\
    Press {} to force exiting without saving.\n\
    Press any other key to continue editing your file."""

RELOAD_FILE_WITHOUT_SAVING = """WARNING: Reload file will discard changes.\n\
    Press F2 to save changes.\n\
    Press {} to reload file and discard all changes.\n\
    Press any other key to continue editing your file."""



""" used for tag input or note input """
def show_input(env):
    pass

def show_menu(env):
    pass



def refresh_main_screens(env):
    env.screens.left.erase()
    env.screens.right.erase()
    env.screens.down.erase()

    env.screens.left.border(0)
    env.screens.right.border(0)
    env.screens.down.border(0)

    env.screens.left.refresh()
    env.screens.right.refresh()
    env.screens.down.refresh()


def rewrite_all_wins(env):
    # refresh_main_screens(env)
    if env.note_management:
        show_notes(env)
    else:
        show_directory_content(env)
    show_file_content(env)
    if not env.edit_allowed:
        show_tags(env)



def print_hint(env, filter_mode=False):
    screen = env.screens.down
    screen.erase()
    screen.border(0)
    size = screen.getmaxyx()

    view_switch = "off" if env.quick_view else "on"
    line_nums_switch = "hide" if env.line_numbers else "show"
    note_switch = "hide" if env.note_highlight else "show"
    B_HELP = {"F1":"help", "F2":"menu", "F3":f"view {view_switch}","F4":"edit", "F5":"copy",
                "F6":"rename", "F8":"delete", "F9":"filter", "F10":"exit"}
    E_HELP = {"F1":"help", "F2":"save", "F3":"view/tag", "F4":"note", "F5":f"{line_nums_switch} lines",
                "F6":f"{note_switch} notes", "F8":"reload", "F9":"filter", "F10":"exit"}
    V_HELP = {"F1":"help", "F4":"edit", "F5":f"{line_nums_switch} lines",
                "F6":f"{note_switch} notes", "F9":"filter", "F10":"exit"}
    T_HELP = {"F1":"help", "F4":"edit tags", "F9":"filter", "F10":"exit"}
    N_HELP = {"F1":"help", "F2":"edit", "F3":"create new", "F4":"insert from menu", 
                "F5":"go to", "F6":"save as typical", "F8":"delete", "F10":"exit"}

    if filter_mode:
        if env.is_brows_mode(): filter_type = "path"
        elif env.is_view_mode(): filter_type = "content"
        elif env.is_tag_mode(): filter_type = "tag"
        else: filter_type = None

        if not filter_type:
            help_dict = {}
        else:
            help_dict = {"F1":"help", "ESC":"exit filter mode", 
                        "F8":"remove all filters", "F9":f"edit {filter_type} filter"}
    elif env.is_brows_mode():
        help_dict = B_HELP
    elif env.is_view_mode():
        help_dict = E_HELP if env.edit_allowed else V_HELP
    elif env.is_tag_mode():
        help_dict = T_HELP
    elif env.is_notes_mode():
        help_dict = N_HELP
    else:
        help_dict = {}


    string = ""
    for key in help_dict:
        hint = " | " + str(key) + ":" + str(help_dict[key])
        if len(string) + len(hint) <= size[1]:
            string += hint
    screen.addstr(1, 1, string[2:])
    screen.refresh()



def print_help(screen, max_cols, max_rows, env, filter_mode=False):
    screen.erase()
    screen.border(0)
    mode = ""
    if filter_mode:
        mode = "FILTER MANAGEMENT"
        actions = {
        "F1": "show this user help",
        "F8": "delete/remove all filters",
        "ESC, F10": "exit filter management",
        "Arrows": "move cursor in user input",
        "Delete, Backspace": "delete symbol in user input",
        "Ascii character": "insert symbol in user input",
        "Enter": "set filter and exit filter management"}

    elif env.is_brows_mode():
        mode = "DIRECTORY BROWSING"
        actions = {
        "F1": "show this user help",
        "F2": "open menu with other functions",
        "F3": "set quick view mode on/off",
        "F4": "opent file for edit",
        "F6": "show/hide cached files (tags, report)",
        "F7": "show/hide project info",
        "F9": "set filter by path",
        "F10": "exit program",
        "TAB": "change focus to file view or edit",
        "Arrows": "brows between files and dirs"}
    elif env.is_view_mode():
        if env.edit_allowed:
            mode = "FILE EDIT"
            actions = {
            "F1": "show this user help",
            "F2": "save file changes",
            "F3": "change to file view/tag mode",
            "F4": "open note management",
            "F5": "show/hide line numbers",
            "F6": "show/hide note highlight",
            "F8": "reload file content from last save",
            "F9": "set filter by content",
            "F10": "exit program",
            "TAB": "change focus to directory browsing or note management",
            "Arrows": "move cursor in file content",
            "Delete, Backspace": "delete symbol in file on current cursor position",
            "Ascii character": "insert symbol in file on current cursor position",
            "Enter": "insert new line in file on current cursor position",
            "CTRL + Up/Down": "jump to prev/next line with note in file",
            "CTRL + L": "reload file content from original buffer",
            "CTRL + R": "remove all notes on current line"}
        else:
            mode = "FILE VIEW"
            actions = {
            "F1": "show this user help",
            "F4": "change to file edit mode",
            "F5": "show/hide line numbers",
            "F6": "show/hide note highlight",
            "F9": "set filter by content",
            "F10": "exit program",
            "TAB": "change focus to tag management",
            "Arrows": "move cursor in file content"}
    elif env.is_tag_mode():
        mode = "TAG MANAGEMENT"
        actions = {
        "F1": "show this user help",
        "F2": "edit current tag",
        "F3": "create new tag",
        "F4": "open file with tags for edit",
        "F8": "delete current tag",
        "F9": "set filter by tag",
        "F10": "exit program",
        "TAB": "change focus to directory browsing",
        "Arrows": "brows between tags"}
    elif env.is_notes_mode():
        mode = "NOTES MANAGEMENT"
        actions = {
        "F1": "show this user help",
        "F2": "edit current note",
        "F3": "create new note",
        "F4": "insert note from saved (typical) notes",
        "F5": "go to current note in file",
        "F6": "save note as typical",
        "F8": "delete current note",
        "F10": "exit note management",
        "TAB": "change focus to file view or edit",
        "Arrows": "brows between notes"}
    if mode and actions:
        exit_message = "Press ESC or F1 to hide user help."
        message = f"*** USER HELP FOR {mode} ***"
        if len(message) >= max_cols:
            message = message[:max_cols-1]
        if len(exit_message) >= max_cols:
            exit_message = exit_message[:max_cols-1]
        screen.addstr(1, 1, exit_message, curses.color_pair(HELP))
        screen.addstr(2, int(max_cols/2-len(message)/2)+1, message, curses.A_NORMAL)
        line = 3
        for key in actions:
            action = actions[key]
            if line < max_rows:
                if len(key)+2 > max_cols:
                    break
                screen.addstr(line, 1, str(key), curses.color_pair(HELP))
                # if it doesnt fit to windows weight
                free_space = max_cols-len(key)-3
                if len(action) > free_space:
                    words = action.split()
                    while words:
                        if line >= max_rows:
                            break
                        part = ""
                        word = words[0]
                        while len(part)+len(word)+1 < free_space:
                            part += " "+word
                            del words[0]
                            if not words:
                                break
                            word = words[0]
                        screen.addstr(line, 3+len(key), str(part), curses.A_NORMAL)
                        line +=1
                else:
                    screen.addstr(line, 3+len(key), str(action), curses.A_NORMAL)
                    line += 1
        screen.refresh()



""" check if file changes are saved or user want to save or discard them """
def file_changes_are_saved(stdscr, env, warning=None, exit_key=None):
    if env.buffer:
        if (env.buffer.is_saved) or (env.buffer.original_buff == env.buffer.lines):
            return True
        else:
            curses_key, str_key = exit_key if exit_key else (ESC, "ESC")
            message = warning if warning else EXIT_WITHOUT_SAVING

            """ print warning message """
            screen = env.screens.right
            screen.erase()
            screen.addstr(1, 1, str(message.format(str_key)), curses.A_BOLD)
            screen.border(0)
            screen.refresh()

            key = stdscr.getch()
            if key == curses_key: # force exit without saving
                return True
            elif key == curses.KEY_F2: # save and exit
                save_buffer(env.file_to_open, env.buffer, env.report)
                return True
            else:
                return False
    else:
        return True



""" show file name/path of currently opened file/directory """
def show_path(screen, path, max_cols):
    while len(path) > max_cols-4:
        path = path.split(os.sep)[1:]
        path = "/".join(path)
    dir_name = " "+str(path)+" "
    screen.addstr(0, int(max_cols/2-len(dir_name)/2), dir_name)
    screen.refresh()


""" center screen """
def show_user_input(screen, user_input, max_rows, max_cols, env, color=None, title=None):
    screen.erase()
    screen.border(0)

    row = 1
    if title:
        screen.addstr(row, 1, title[:max_cols-1], color if color else curses.A_NORMAL)
        row += 1

    last_row = row
    last_col = 1
    if user_input:
        max_cols -= 1
        user_input_str = ''.join(user_input.text)
        # if len(user_input_str) > max_cols:
        words = re.split(r'(\S+)',user_input_str) # split string into list of words and spaces
        split_words = []
        for word in words:
            # if any word is longer than window, split it
            if len(word) >= max_cols:
                while len(word) >= max_cols:
                    part = word[:max_cols-1]
                    # log(part)
                    split_words.append(part)
                    word = word[max_cols-1:]
            split_words.append(word)

        words = split_words
        while words:
            if row >= max_rows:
                break
            part = ""
            word = words[0]
            while len(part)+len(word) < max_cols:
                part += word
                del words[0]
                if not words:
                    break
                word = words[0]
            # log(part)
            screen.addstr(row, 1, str(part), curses.A_NORMAL)
            last_col = 1+len(part)
            last_row = row
            row +=1

    screen.refresh()
    return last_row, last_col


""" filter on last row in screen """
def show_filter(screen, user_input, max_rows, max_cols, env):
    if user_input:
        user_input_str = ''.join(user_input.text)
        if user_input.col_shift > 0 and len(user_input_str) > user_input.col_shift:
            user_input_str = user_input_str[user_input.col_shift + 1:]

    if not user_input.text:
        # show default message with example usage of filter
        empty_message = ""
        if env.is_brows_mode(): empty_message = env.messages['empty_path_filter']
        elif env.is_view_mode(): empty_message = env.messages['empty_content_filter']
        elif env.is_tag_mode(): empty_message = env.messages['empty_tag_filter']
        empty_message += " "*(max_cols-1-len(empty_message))
        screen.addstr(max_rows, 1, empty_message[:max_cols-1], curses.color_pair(FILTER) | curses.A_ITALIC)
    else:
        user_input_str += " "*(max_cols-1-len(user_input_str))
        screen.addstr(max_rows, 1, user_input_str[:max_cols-1], curses.color_pair(FILTER))
    screen.refresh()




""" browsing directory """
def show_directory_content(env):
    screen, win = env.screens.left, env.windows.brows

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1

    cwd = Directory(env.filter.project, files=env.filter.files) if env.filter_not_empty() else env.cwd
    dirs, files = cwd.get_shifted_dirs_and_files(win.row_shift)


    """ print borders """
    screen.erase()
    if env.is_brows_mode():
        screen.attron(curses.color_pair(BORDER))
        screen.border(0)
        screen.attroff(curses.color_pair(BORDER))
    else:
        screen.border(0)

    """ print hint for user """
    print_hint(env)


    try:
        """ show dir name """
        show_path(screen, cwd.path, max_cols)

        """ show dir content """
        if cwd.is_empty():
            if env.filter_not_empty():
                screen.addstr(1, 1, "* No file matches with current filter *", curses.A_NORMAL | curses.A_BOLD)
            else:
                screen.addstr(1, 1, "* This directory is empty *", curses.A_NORMAL | curses.A_BOLD)
        else:
            i=1
            for dir_name in dirs:
                if i > max_rows:
                    break
                elif i == max_rows and env.filter:
                    if env.filter.path:
                        break
                coloring = (curses.color_pair(SELECT) if i+win.row_shift == win.cursor.row+1 else curses.A_NORMAL)
                screen.addstr(i, 1, str(dir_name[:max_cols-2])+"/", coloring | curses.A_BOLD)
                i+=1
            for file_name in files:
                if i > max_rows:
                    break
                elif i == max_rows and env.filter:
                    if env.filter.path:
                        break
                coloring = curses.color_pair(SELECT) if i+win.row_shift == win.cursor.row+1 else curses.A_NORMAL
                screen.addstr(i, 1, str(file_name[:max_cols-1]), coloring)
                i+=1

        """ show path filter if there is one """
        if env.filter:
            if env.filter.path:
                user_input = UserInput()
                user_input.text = env.filter.path
                show_filter(screen, user_input, max_rows, max_cols, env)

    except Exception as err:
        log("show directory | "+str(err))
    finally:
        screen.refresh()


""" view file content """
def show_file_content(env):
    screen = env.screens.right if env.edit_allowed else env.screens.right_up
    win = env.windows.edit if env.edit_allowed else env.windows.view

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1

    buffer = env.buffer
    report = env.report
    shift = len(env.line_numbers)+1 if env.line_numbers else 0 # shift for line numbers


    """ print borders """
    screen.erase()
    if env.is_view_mode():
        screen.attron(curses.color_pair(BORDER))
        screen.border(0)
        screen.attroff(curses.color_pair(BORDER))
    else:
        screen.border(0)

    """ print hint for user """
    print_hint(env)

    """ if there is no buffer, show empty window """
    if buffer is None:
        screen.refresh()
        return

    """ highlight lines with notes """
    colored_lines = []
    if env.note_highlight and report:
        for key in report.code_review:
            colored_lines.append(int(key))


    try:
        """ show file name """
        show_path(screen, buffer.path, max_cols+(shift if env.line_numbers else 1))

        """ show file content """
        if buffer:
            for row, line in enumerate(buffer[win.row_shift : max_rows + win.row_shift]):
                if row > max_rows or (row == max_rows and env.tag_filter_on()):
                    break

                """ replace tab with spaces in line """
                line = line.replace("\t", " "*env.tab_size)

                if (row + win.begin_y == win.cursor.row - win.row_shift) and (win.col_shift > 0):
                    line = line[win.col_shift + 1:]
                if len(line) > max_cols - 1:
                    line = line[:max_cols - 1]

                """ set color """
                if (row+1+win.row_shift in colored_lines):
                    color = curses.color_pair(NOTE_HIGHLIGHT)            
                else:
                    color = curses.A_NORMAL 
                if env.specific_line_highlight is not None:
                    highlight_line, highlight_col = env.specific_line_highlight
                    if (row+1 == highlight_line):
                        color = highlight_col

                """ print line """
                if env.line_numbers: # row+1 bcs row starts from 0
                    screen.addstr(row+1, 1, str(row+1+win.row_shift), curses.color_pair(LINE_NUM))
                screen.addstr(row+1, 1+shift, line, color)

        
        """ show content filter if there is one """
        if env.content_filter_on():
            user_input = UserInput()
            user_input.text = env.filter.content
            show_filter(screen, user_input, max_rows, max_cols, env)

    except Exception as err:
        log("show file | "+str(err))
    finally:
        screen.refresh()


""" tag management """
def show_tags(env):
    screen, win = env.screens.right_down, env.windows.tag

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1

    tags = env.tags


    """ print borders """
    screen.erase()
    if env.is_tag_mode():
        screen.attron(curses.color_pair(BORDER))
        screen.border(0)
        screen.attroff(curses.color_pair(BORDER))
    else:
        screen.border(0)

    """ if there is no tags, then show empty window """
    if tags is None:
        screen.refresh()
        return


    try:
        """ show file name """
        show_path(screen, tags.path, max_cols)

        """ show tags """
        if tags.data:
            for row, name in enumerate(tags.data):
                if row > max_rows or (row == max_rows and env.tag_filter_on()):
                    break

                """ set color """
                if row+win.row_shift == win.cursor.row and env.is_tag_mode():
                    coloring = curses.color_pair(SELECT)
                else:
                    coloring = curses.A_NORMAL

                """ format and print tag """
                params = tags.data[name]
                str_params = "(" + ",".join(map(str,params)) + ")"
                line = "#"+str(name)+str_params
                if len(line) > max_cols -1:
                    line = line[:max_cols - 1]
                screen.addstr(row+1, 1, line, coloring)

        """ show tag filter if there is one """
        if env.tag_filter_on():
            user_input = UserInput()
            user_input.text = env.filter.tag
            show_filter(screen, user_input, max_rows, max_cols, env)

    except Exception as err:
        log("show tags | "+str(err))
    finally:
        screen.refresh()


def show_notes(env):
    screen, win = env.screens.left, env.windows.notes

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1

    report = env.report

    """ print borders """
    screen.erase()
    if env.is_notes_mode():
        screen.attron(curses.color_pair(BORDER))
        screen.border(0)
        screen.attroff(curses.color_pair(BORDER))
    else:
        screen.border(0)

    """ if there is no report with notes, then show empty window """
    if report is None:
        screen.refresh()
        return

    try:
        """ show file name """
        show_path(screen, report.path, max_cols)

        """ show report """
        # if False:
        if report.code_review:
            row = 0
            # {line : { row1: ['note1'], row2: ['note2', 'note3']} }
            notes = get_visible_notes(report, max_rows)
            for row, note in enumerate(notes):
                """ set color """
                if row+win.row_shift == win.cursor.row and env.is_notes_mode():
                    coloring = curses.color_pair(SELECT)
                else:
                    coloring = curses.A_NORMAL

                if len(note) > max_cols - 1:
                    note = note[:max_cols - 1]
                screen.addstr(row+1, 1, note, coloring)

    except Exception as err:
        log("show notes | "+str(err))
    finally:
        screen.refresh()


def get_visible_notes(report, max_rows):
    row = 0
    result = []
    for line in sorted(report.code_review):
        for col in sorted(report.code_review[line]):
            notes = report.code_review[line][col]
            for note in notes:
                if row >= max_rows:
                    return result
                text = str(line)+":"+str(col)+":"+str(note)
                result.append(text)
                row +=1
    return result
