import curses
import os
import re
import traceback

from modules.buffer import UserInput
from modules.directory import Directory

from utils.highlighter import parse_code
from utils.loading import save_buffer, load_solution_tags, load_tests_tags
from utils.coloring import *
from utils.logger import *
from utils.parsing import parse_solution_info_visualization, parse_solution_info_predicate
from utils.match import match_regex, is_root_project_dir

ESC = 27


EXIT_WITHOUT_SAVING = """WARNING: Exit without saving.\n\
    Press F2 to save and exit.\n\
    Press {} to force exiting without saving.\n\
    Press any other key to continue editing your file."""

RELOAD_FILE_WITHOUT_SAVING = """WARNING: Reload file will discard changes.\n\
    Press F2 to save changes.\n\
    Press {} to reload file and discard all changes.\n\
    Press any other key to continue editing your file."""

EMPTY_PATH_FILTER_MESSAGE = "add path filter... ex: test1/unit "
EMPTY_CONTENT_FILTER_MESSAGE = "add content filter... ex: def test1 "
EMPTY_TAG_FILTER_MESSAGE = "add tag filter... ex: plagiat(^[0-5]$) "


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
    """ print hint for user """
    print_hint(env)

    if env.show_notes:
        show_notes(env)
    else:
        show_directory_content(env)
    show_file_content(env)
    if env.show_tags:
        show_tags(env)

def rewrite_brows(env, hint=True):
    if hint:
        print_hint(env)
    show_directory_content(env)

def rewrite_file(env, hint=True):
    if hint:
        print_hint(env)
    show_file_content(env)
    if env.show_tags:
        show_tags(env)

def rewrite_notes(env, hint=True):
    if hint:
        print_hint(env)
    show_notes(env)



def print_hint(env):
    screen = env.screens.down
    screen.erase()
    screen.border(0)
    size = screen.getmaxyx()

    line_nums_switch = "hide" if env.line_numbers else "show"
    cached_files = "hide" if env.show_cached_files else "show"
    # note_switch = "hide" if env.note_highlight else "show"
    tags_switch = "hide" if env.show_tags else "show"
    view_switch = "off" if env.quick_view else "on"

    typical_note = "save as"
    if env.is_notes_mode() and env.report is not None:
        if len(env.report.data) > 0 and len(env.report.data) >= env.windows.notes.cursor.row:
            if env.report.data[env.windows.notes.cursor.row].is_typical(env):
                typical_note = "unsave from"

    N_HELP = {"F1":"help", "F2":"edit", "F3":"create new", "F4":"insert from menu", 
                "F5":"go to", "F6":f"{typical_note} typical", "F8":"delete", "F10":"exit"}

    B_HELP = {"F1":"help", "F2":"menu", "F3":f"view {view_switch}","F4":"edit",
                "F6":f"{cached_files} cached files", "F8":"delete", "F9":"filter", "F10":"exit"}

    E_HELP = {"F1":"help", "F2":"save", "F3":f"{tags_switch} tags", "F4":"edit file", "F5":f"{line_nums_switch} lines",
                "F6":"note highlight", "F7":"note mgmt", "F8":"reload", "F9":"show typical notes", "ESC":"manage file", "F10":"exit"}

    T_HELP = {"F1":"help", "F3":"new tag", "F4":"edit tags", "F8":"delete", "F9":"filter", "F10":"exit"}

    if env.is_filter_mode():
        if env.is_brows_mode(): filter_type = "path"
        elif env.is_view_mode(): filter_type = "content"
        elif env.is_tag_mode(): filter_type = "tag"
        else: filter_type = None

        F_HELP = {"F1":"help", "ESC":"exit filter mode", "F4":"aggregate",
                "F8":"remove all filters", "F9":f"edit {filter_type} filter"}
        help_dict = {} if not filter_type else F_HELP
    elif env.is_brows_mode():
        help_dict = B_HELP
    elif env.is_view_mode():
        help_dict = E_HELP
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


""" custom_help = (exit_message, title, dictionary)"""
def print_help(screen, max_cols, max_rows, env, custom_help=None):
    screen.erase()
    screen.border(0)
    mode = ""
    if custom_help is None:
        if env.is_filter_mode():
            mode = "FILTER MANAGEMENT"
            actions = {
            "F1": "show this user help",
            "F4": "aggregate by same tags file",
            "F8": "delete/remove all filters",
            "F10": "exit program",
            "ESC": "exit filter management",
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
            "F9": "set filter by path",
            "F10": "exit program",
            "TAB": "change focus to file view or edit",
            "Arrows": "brows between files and dirs"}
        elif env.is_view_mode():
            if env.show_tags:
                tab_action = "change focus to tag management"
            elif env.show_notes:
                tab_action = "change focus to note management"
            else:
                tab_action = "change focus to directory browsing"

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
            "TAB": f"{tab_action}",
            "Arrows": "move cursor in file content",
            "Delete, Backspace": "delete symbol in file on current cursor position",
            "Ascii character": "insert symbol in file on current cursor position",
            "Enter": "insert new line in file on current cursor position",
            "CTRL + Up/Down": "jump to prev/next line with note in file",
            "CTRL + L": "reload file content from original buffer",
            "CTRL + R": "remove all notes on current line"}
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
            "F10": "exit program",
            "ESC": "exit note management",
            "TAB": "change focus to file view or edit",
            "Arrows": "brows between notes"}
        else:
            screen.refresh()
        exit_message = "Press ESC or F1 to hide user help."
        title = f"*** USER HELP FOR {mode} ***"

    else:
        exit_message = custom_help[0]
        title = custom_help[1]
        actions = custom_help[2]

    line = 1
    if exit_message:
        if len(exit_message) >= max_cols:
            exit_message = exit_message[:max_cols-1]
        screen.addstr(line, 1, exit_message, curses.color_pair(COL_HELP))
        line += 1
    if title:
        if len(title) >= max_cols:
            title = title[:max_cols-1]
        screen.addstr(line, int(max_cols/2-len(title)/2)+1, title, curses.A_NORMAL)
        line += 1
    for key in actions:
        action = actions[key]
        if line < max_rows:
            if len(key)+2 > max_cols:
                break
            screen.addstr(line, 1, str(key), curses.color_pair(COL_HELP))
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
    # screen.refresh()


""" center screen """
def show_user_input(screen, user_input, max_rows, max_cols, env, color=None, title=None):
    screen.erase()
    screen.border(0)

    row = 0
    if title:
        screen.addstr(row+1, 1, title[:max_cols], color if color else curses.A_NORMAL)
        row += 1

    cnt_total = 0 # counter of total processed (printed) characters
    cnt_on_line = 0 # counter of processed characters on one line
    current_cursor = row, cnt_on_line

    if user_input:
        user_input_str = ''.join(user_input.text)
        # if len(user_input_str) > max_cols:
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

        words = split_words
        while words:
            if row >= max_rows:
                break
            line = ""
            word = words[0] # get first word
            cnt_on_line = 0 # reset counter on new line
            while len(line)+len(word) < max_cols: # check if the word fits in the line
                """ add word to the line """
                line += word
                del words[0]

                """ get cursor position """
                if cnt_total == user_input.pointer: # all characters (from begining to current pointer) were processed
                    current_cursor = row, cnt_on_line # save current cursor position: row + counter of characters on this row (as column)
                for _ in word: # process new added word in line, by its symbols (characters)
                    cnt_total += 1
                    cnt_on_line += 1
                    if cnt_total == user_input.pointer: # with each character check if all were processed
                        current_cursor = row, cnt_on_line
                if not words:
                    break
                word = words[0] # get next word
            screen.addstr(row+1, 1, str(line), curses.A_NORMAL)
            row +=1

    screen.refresh()
    return current_cursor


""" filter on last row in screen """
def show_filter(screen, user_input, max_rows, max_cols, env):
    if user_input:
        user_input_str = ''.join(user_input.text)
        if user_input.col_shift > 0 and len(user_input_str) > user_input.col_shift:
            user_input_str = user_input_str[user_input.col_shift + 1:]

    if not user_input.text:
        # show default message with example usage of filter
        empty_message = ""
        if env.is_brows_mode(): empty_message = EMPTY_PATH_FILTER_MESSAGE
        elif env.is_view_mode(): empty_message = EMPTY_CONTENT_FILTER_MESSAGE
        elif env.is_tag_mode(): empty_message = EMPTY_TAG_FILTER_MESSAGE
        empty_message += " "*(max_cols-1-len(empty_message))
        screen.addstr(max_rows, 1, empty_message[:max_cols-1], curses.color_pair(COL_FILTER) | curses.A_ITALIC)
    else:
        user_input_str += " "*(max_cols-1-len(user_input_str))
        screen.addstr(max_rows, 1, user_input_str[:max_cols-1], curses.color_pair(COL_FILTER))
    screen.refresh()




""" browsing directory """
def show_directory_content(env):
    screen, win = env.screens.left, env.windows.brows

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1

    # cwd = Directory(env.filter.root, files=env.filter.files) if env.filter_not_empty() else env.cwd
    cwd = env.cwd
    dirs, files = cwd.get_shifted_dirs_and_files(win.row_shift)


    """ print borders """
    screen.erase()
    if env.is_brows_mode():
        screen.attron(curses.color_pair(COL_BORDER))
        screen.border(0)
        screen.attroff(curses.color_pair(COL_BORDER))
    else:
        screen.border(0)


    solution_id = None
    if is_root_project_dir(cwd.path) and cwd.proj is not None:
        solution_id = cwd.proj.solution_id

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
                if i > max_rows or (i == max_rows and env.path_filter_on()):
                    break
                coloring = (curses.color_pair(COL_SELECT) if i+win.row_shift == win.cursor.row+1 else curses.A_NORMAL)
                txt = str(dir_name[:max_cols-2])+"/"
                screen.addstr(i, 1, txt, coloring | curses.A_BOLD)

                if env.show_solution_info and solution_id is not None:
                    if match_regex(solution_id, dir_name):
                        solution_dir = os.path.join(cwd.path, dir_name)
                        infos = get_info_for_solution(env, cwd.proj, solution_dir) # !! vykreslovat zprava
                        if infos:
                            space = 2 # refers to visual space between dir name and its info
                            stop = len(txt)+space
                            x = max_cols
                            for item in infos:
                                info, col = item
                                if x-len(info)-1 <= stop:
                                    break
                                x = x-len(info)-1
                                color = (curses.color_pair(COL_SELECT) if i+win.row_shift == win.cursor.row+1 else col)
                                screen.addstr(i, x, str(info)+' ', color)
                            if x > stop: # empty space between dir name and its info
                                screen.addstr(i, len(txt)+1, ' '*(x-stop-1+space), coloring)

                i+=1
            for file_name in files:
                if i > max_rows or (i == max_rows and env.path_filter_on()):
                    break
                coloring = curses.color_pair(COL_SELECT) if i+win.row_shift == win.cursor.row+1 else curses.A_NORMAL
                screen.addstr(i, 1, str(file_name[:max_cols-1]), coloring)
                i+=1

        """ show path filter if there is one """
        if env.filter:
            if env.filter.path:
                user_input = UserInput()
                user_input.text = env.filter.path
                show_filter(screen, user_input, max_rows, max_cols, env)

    except Exception as err:
        log("show directory | "+str(err)+" | "+str(traceback.format_exc()))
    finally:
        screen.refresh()


def rewrite_one_line_in_file(env, line_num):
    screen = env.screens.right_up if env.show_tags else env.screens.right
    win = env.windows.view if env.show_tags else env.windows.edit
    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1

    buffer = env.buffer
    report = env.report

    shift = len(env.line_numbers)+1 if env.line_numbers else 1 # shift for line numbers

    if buffer is not None:
        line = buffer[line_num-1]
        tokens = parse_code(buffer.path, line)

        if tokens is not None:
            y = line_num-win.row_shift
            screen.move(y,1+shift)
            position = 0
            text_color = curses.A_NORMAL
            for token in tokens:
                style, text = token
                _,x = screen.getyx()

                """ replace tab with spaces in line """
                text = text.replace("\t", " "*env.tab_size)

                text_color = curses.color_pair(style)
                if env.specific_line_highlight is not None:
                    highlight_line, highlight_color = env.specific_line_highlight
                    if (y == highlight_line):
                        text_color = highlight_color

                """ column shift correction """
                if (y-1+win.begin_y == win.cursor.row-win.row_shift) and (win.col_shift > 0):
                    old_position = position
                    position += len(text[:max_cols-position-1]) # position simulates token printing
                    if position < win.col_shift:
                        continue
                    if old_position <= win.col_shift: # token text is between pages (before and after col shift position)
                        text = text[win.col_shift-old_position+1:]
                        x = 1+shift
                else:
                    position = 0 # reset position

                """ print token """
                if text == '\n':
                    break
                else:
                    if x+len(text) > max_cols+shift:
                        screen.addstr(y, x, str(text[:max_cols+shift-x]), text_color)
                        break
                    else:
                        screen.addstr(y, x, str(text), text_color)
            _,x = screen.getyx()
            screen.addstr(y, x, str(' '*(max_cols+shift-x)), text_color)
        else:
            line = line.replace("\t", " "*env.tab_size)
            line = line + str(' '*(max_cols-len(line)))

            if (line_num-1+win.begin_y == win.cursor.row-win.row_shift) and (win.col_shift > 0):
                line = line[win.col_shift + 1:]
            if len(line) > max_cols - 1:
                line = line[:max_cols - 1]

            text_color = curses.A_NORMAL
            if env.specific_line_highlight is not None:
                highlight_line, highlight_color = env.specific_line_highlight
                if (line_num == highlight_line):
                    text_color = highlight_color
            """ print line """
            screen.addstr(line_num, 1+shift, line, text_color)

        screen.refresh()



""" view file content """
def show_file_content(env):
    screen = env.screens.right_up if env.show_tags else env.screens.right
    win = env.windows.view if env.show_tags else env.windows.edit


    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1

    buffer = env.buffer
    report = env.report

    #  OPTION A : note highlight on full line + screens.py line 160 shift
    # shift = len(env.line_numbers)+1 if env.line_numbers else 0 # shift for line numbers
    #  OPTION B : note highlight on line number
    #  OPTION C : note highlight on symbol '|' before line + screens.py line 160 shift
    # shift = len(env.line_numbers)+1 if env.line_numbers else 1 # shift for line numbers
    shift = win.line_num_shift

    """ try to get syntax highlight """
    if buffer is not None:
        tokens = parse_code(buffer.path, '\n'.join(buffer[win.row_shift:]))

    screen.erase()
    """ print border """
    if env.is_view_mode():
        screen.attron(curses.color_pair(COL_BORDER))
        screen.border(0)
        screen.attroff(curses.color_pair(COL_BORDER))
    else:
        screen.border(0)

    """ if there is no buffer, show empty window """
    if buffer is None:
        screen.refresh()
        return

    """ show file name """
    show_path(screen, buffer.path, max_cols+(shift if env.line_numbers else 1))

    """ highlight lines with notes """
    colored_lines = []
    if env.note_highlight and report:
        for note in report.data:
            colored_lines.append(int(note.row))


    try:
        """ show file content """
        if buffer:
            if tokens is not None:
                # =============== print with syntax highlight ===============
                screen.move(1,1+shift)
                skip = False
                position = 0
                for token in tokens:
                    style, text = token
                    y,x = screen.getyx()

                    if y > max_rows or (y == max_rows and env.content_filter_on()) or y+win.row_shift > len(buffer):
                        break
                    if x == 0:
                        x = 1+shift

                    if skip: # skip tokens with no newline bcs we are over screen horizontally
                        if text.startswith('\n'):
                            skip = False
                        else:
                            continue

                    """ replace tab with spaces in line """
                    text = text.replace("\t", " "*env.tab_size)

                    #  OPTION A : note highlight on full line
                    # """ set color for line numbers and for line text """
                    # if (y + win.row_shift in colored_lines):
                    #     text_color = curses.color_pair(COL_NOTE)
                    # else:
                    #     text_color = curses.color_pair(style)
                    # if env.specific_line_highlight is not None:
                    #     highlight_line, highlight_color = env.specific_line_highlight
                    #     if (y == highlight_line):
                    #         text_color = highlight_color

                    # """ print line number """
                    # if env.line_numbers:
                    #     screen.addstr(y, 1, str(y+win.row_shift), curses.color_pair(COL_LINE_NUM))


                    #  OPTION B : note highlight on line number
                    """ set color for line numbers and for line text """
                    if (y + win.row_shift in colored_lines):
                        line_num_color = curses.color_pair(COL_NOTE)
                    else:
                        line_num_color = curses.color_pair(COL_LINE_NUM)

                    text_color = curses.color_pair(style)
                    if env.specific_line_highlight is not None:
                        highlight_line, highlight_color = env.specific_line_highlight
                        if (y == highlight_line):
                            text_color = highlight_color

                    """ print line number """
                    if env.line_numbers:
                        screen.addstr(y, 1, str(y+win.row_shift), line_num_color)
                    else:
                        screen.addstr(y, 1, " ", line_num_color)

                    #  OPTION C : note highlight on symbol '|' before line
                    # """ set color for line numbers and for line text """
                    # if (y + win.row_shift in colored_lines):
                    #     line_num_color = curses.color_pair(HL_DARK_YELLOW)
                    # else:
                    #     line_num_color = curses.color_pair(HL_DARK_GRAY)

                    # text_color = curses.color_pair(style)
                    # if env.specific_line_highlight is not None:
                    #     highlight_line, highlight_color = env.specific_line_highlight
                    #     if (y == highlight_line):
                    #         text_color = highlight_color

                    # """ print line number """
                    # if env.line_numbers:
                    #     screen.addstr(y, 1, str(y+win.row_shift), curses.color_pair(COL_LINE_NUM))
                    #     screen.addstr(y, shift, "|", line_num_color)
                    # else:
                    #     screen.addstr(y, 1, "|", line_num_color)


                    """ column shift correction """
                    if (y-1+win.begin_y == win.cursor.row-win.row_shift) and (win.col_shift > 0): # y-1 bcs we start at line 1 not 0
                        old_position = position
                        position += len(text[:max_cols-position-1]) # position simulates token printing
                        if position < win.col_shift:
                            continue
                        if old_position <= win.col_shift: # token text is between pages (before and after col shift position)
                            text = text[win.col_shift-old_position+1:]
                            x = 1+shift
                    else:
                        position = 0 # reset position

                    """ print token """
                    if text == '\n':
                        screen.move(y+1,1+shift)
                    else:
                        if x+len(text) > max_cols+shift:
                            screen.addstr(y, x, str(text[:max_cols+shift-x]), text_color)
                            skip = True
                        else:
                            screen.addstr(y, x, str(text), text_color)
            else:
                # =============== print without syntax highlight ===============
                for row, line in enumerate(buffer[win.row_shift : max_rows + win.row_shift]):
                    if row > max_rows or (row == max_rows and env.content_filter_on()):
                        break

                    """ replace tab with spaces in line """
                    line = line.replace("\t", " "*env.tab_size)

                    if (row + win.begin_y == win.cursor.row - win.row_shift) and (win.col_shift > 0):
                        line = line[win.col_shift + 1:]
                    if len(line) > max_cols - 1:
                        line = line[:max_cols - 1]


                    #  OPTION A : note highlight on full line
                    # """ set color for line numbers and for line text """
                    # if (row+1+win.row_shift in colored_lines):
                        # text_color = curses.color_pair(COL_NOTE)
                    # else:
                    #     text_color = curses.A_NORMAL
                    # if env.specific_line_highlight is not None:
                    #     highlight_line, highlight_color = env.specific_line_highlight
                    #     if (row+1 == highlight_line):
                    #         text_color = highlight_color

                    # """ print line number """
                    # if env.line_numbers: # row+1 bcs row starts from 0
                    #     screen.addstr(row+1, 1, str(row+1+win.row_shift), curses.color_pair(COL_LINE_NUM))


                    #  OPTION B : note highlight on line number
                    """ set color for line numbers and for line text """
                    if (row+1+win.row_shift in colored_lines):
                        line_num_color = curses.color_pair(COL_NOTE)
                    else:
                        line_num_color = curses.color_pair(COL_LINE_NUM)

                    text_color = curses.A_NORMAL
                    if env.specific_line_highlight is not None:
                        highlight_line, highlight_color = env.specific_line_highlight
                        if (row+1 == highlight_line):
                            text_color = highlight_color

                    """ print line number """
                    if env.line_numbers: # row+1 bcs row starts from 0
                        screen.addstr(row+1, 1, str(row+1+win.row_shift), line_num_color)
                    else:
                        screen.addstr(row+1, 1, " ", line_num_color)


                    #  OPTION C : note highlight on symbol '|' before line
                    # """ set color for line numbers and for line text """
                    # if (row+1+win.row_shift in colored_lines):
                    #     line_num_color = curses.color_pair(HL_DARK_YELLOW)
                    # else:
                    #     line_num_color = curses.color_pair(HL_DARK_GRAY)

                    # text_color = curses.A_NORMAL
                    # if env.specific_line_highlight is not None:
                    #     highlight_line, highlight_color = env.specific_line_highlight
                    #     if (row+1 == highlight_line):
                    #         text_color = highlight_color

                    # """ print line number """
                    # if env.line_numbers: # row+1 bcs row starts from 0
                    #     screen.addstr(row+1, 1, str(row+1+win.row_shift), curses.color_pair(COL_LINE_NUM))
                    #     screen.addstr(row+1, shift, "|", line_num_color)
                    # else:
                    #     screen.addstr(row+1, 1, "|", line_num_color)


                    """ print line """
                    screen.addstr(row+1, 1+shift, line, text_color)
        else:
            #  OPTION A : note highlight on full line
            # """ print line number """
            # if env.line_numbers:
            #     screen.addstr(1, 1, "1", curses.color_pair(COL_LINE_NUM))


            #  OPTION B : note highlight on line number
            """ set color for line numbers """
            if (1 in colored_lines):
                line_num_color = curses.color_pair(COL_NOTE)            
            else:
                line_num_color = curses.color_pair(COL_LINE_NUM)

            """ print line number """
            if env.line_numbers:
                screen.addstr(1, 1, "1", line_num_color)
            else:
                screen.addstr(1, 1, " ", line_num_color)


            #  OPTION C : note highlight on symbol '|' before line
            # """ set color for line numbers and for line text """
            # if (1 in colored_lines):
            #     line_num_color = curses.color_pair(HL_DARK_YELLOW)
            # else:
            #     line_num_color = curses.color_pair(HL_DARK_GRAY)

            # """ print line number """
            # if env.line_numbers:
            #     screen.addstr(1, 1, "1", curses.color_pair(COL_LINE_NUM))
            #     screen.addstr(1, 2, "|", line_num_color)
            # else:
            #     screen.addstr(1, 1, "|", line_num_color)


        """ show content filter if there is one """
        if env.content_filter_on():
            user_input = UserInput()
            user_input.text = env.filter.content
            show_filter(screen, user_input, max_rows, max_cols+shift, env)
            # show_filter(screen, user_input, max_rows, max_cols, env)

    except Exception as err:
        log("show file | "+str(err)+" | "+str(traceback.format_exc()))
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
        screen.attron(curses.color_pair(COL_BORDER))
        screen.border(0)
        screen.attroff(curses.color_pair(COL_BORDER))
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
            i = 1
            for row, name in enumerate(tags.data):
                if row < win.row_shift:
                    continue
                if i > max_rows or (i == max_rows and env.tag_filter_on()):
                    break

                """ set color """
                if i-1+win.row_shift == win.cursor.row and env.is_tag_mode():
                    coloring = curses.color_pair(COL_SELECT)
                else:
                    coloring = curses.A_NORMAL

                """ format and print tag """
                params = tags.data[name]
                str_params = "(" + ",".join(map(str,params)) + ")"
                line = "#"+str(name)+str_params
                if len(line) > max_cols -1:
                    line = line[:max_cols - 1]
                screen.addstr(i, 1, line, coloring)
                i+=1

        """ show tag filter if there is one """
        if env.tag_filter_on():
            user_input = UserInput()
            user_input.text = env.filter.tag
            show_filter(screen, user_input, max_rows, max_cols, env)

    except Exception as err:
        log("show tags | "+str(err)+" | "+str(traceback.format_exc()))
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
        screen.attron(curses.color_pair(COL_BORDER))
        screen.border(0)
        screen.attroff(curses.color_pair(COL_BORDER))
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
        if report.data:
            for row, note in enumerate(report.data[win.row_shift : max_rows + win.row_shift]):
                if row > max_rows:
                    break

                """ replace tab with spaces in note """
                text = note.text.replace("\t", " "*env.tab_size)

                star = "*" if note.is_typical(env) else " "
                line = star + str(note.row) + ":" + str(note.col) + ":" + text

                if (row + win.begin_y == win.cursor.row - win.row_shift) and (win.col_shift > 0):
                    line = line[win.col_shift + 1:]
                if len(line) > max_cols - 1:
                    line = line[:max_cols - 1]

                """ set color """
                if row+win.row_shift == win.cursor.row and env.is_notes_mode():
                    color = curses.color_pair(COL_SELECT)
                else:
                    color = curses.A_NORMAL

                """ print line """
                screen.addstr(row+1, 1, line, color)

    except Exception as err:
        log("show notes | "+str(err)+" | "+str(traceback.format_exc()))
    finally:
        screen.refresh()


def show_menu(screen, win, menu_options, max_rows, max_cols, env, keys=None, color=None, title=None):
    screen.erase()
    screen.border(0)

    row = 0
    if title:
        screen.addstr(row+1, 1, title[:max_cols], color if color else curses.A_NORMAL)
        row += 1

    # shift = len(str(min(max_rows,len(menu_options))))+1

    try:
        """ show options """
        if len(menu_options) > 0:
            for option in menu_options[win.row_shift:]:
                if row+1 > max_rows:
                    break

                """ set color """
                if row+win.row_shift == win.cursor.row+1: # +1
                    coloring = curses.color_pair(COL_SELECT)
                else:
                    coloring = curses.A_NORMAL

                if keys is not None and len(keys) > row-1+win.row_shift:
                    key = keys[row-1+win.row_shift]
                else:
                    key = row+win.row_shift
                screen.addstr(row+1, 1, str(key), curses.color_pair(COL_HELP))
                shift = len(str(key))+1
                screen.addstr(row+1, 1+shift, str(option[:max_cols-(1+shift)]), coloring)
                row += 1
        else:
            screen.addstr(row+1, 1, "* There is no option to select from menu *", curses.A_NORMAL | curses.A_BOLD)

    except Exception as err:
        log("show menu | "+str(err)+" | "+str(traceback.format_exc()))
    finally:
        screen.refresh()


"""
    3. for info in solution_info -- citam zprava a pridavam zlava
    
    c) for predicate in predicates -- resp while predicate not matches
        1. spracuj predicate
        2. vyhodnot predicate
        3. ak matchol, konci a vrat farbu ak je definovana, inak vrat Normal farbu
        4. ak nematchol pokracuj v cykle
        5. ak uz nie su dalsie predicates --> nezobrazuj info a chod dalej
    d) ak mas co zobrazit, pridaj zlava hodnotu v danej farbe + 1 medzeru
    e) ak nemas co zobrazit, pridaj zlava medzeru*length + 1 medzeru
"""

def get_info_for_solution(env, proj, solution_dir):
    try:
        # get required solution info for project
        solution_info = proj.get_only_valid_solution_info()
        if not solution_info:
            return []

        result = []
        infos_dict = {} # 'identifier' = (match, visualization, color)
        solution_info = sorted(solution_info, key=lambda d: d['identifier'])

        for info in solution_info:
            identifier = info['identifier']
            predicates = info['predicates']

            # parse visualization and length
            visualization, length = parse_solution_info_visualization(info, solution_dir)

            # check predicates and get color
            if length is not None:
                color = curses.A_NORMAL
                if visualization is None:
                    match, visual = False, ' '*length
                else:
                    predicate_matches = False if len(predicates)>0 else True
                    for predicate in predicates:
                        # match first predicate and get its color
                        predicate_matches, col = parse_solution_info_predicate(predicate, solution_dir)
                        if predicate_matches:
                            color = col
                            break
                    match = predicate_matches
                    visual = visualization if match else ' '*length

                if identifier not in infos_dict:
                    infos_dict[identifier] = (match, visual, color)
                else:
                    # if there is more than one info with this identifier
                    last_match, _, _ = infos_dict[identifier]
                    if not last_match: # if the last one failed to match, add second one
                        infos_dict[identifier] = (match, visual, color)

        for info in infos_dict:
            _, visual, color = infos_dict[info]
            result.append((visual, color))

        return result
    except Exception as err:
        log("get info for solution | "+str(err))
        return []

