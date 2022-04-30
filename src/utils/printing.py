import curses
import os
import re
import shutil
import traceback

from controls.functions import *

from modules.buffer import UserInput
from modules.directory import Directory

from utils.highlighter import parse_code
from utils.loading import save_buffer_to_file, save_report_to_file, load_testcase_tags
from utils.coloring import *
from utils.logger import *
from utils.match import match_regex, is_root_project_dir, is_testcase_result_dir
from utils.history import history_test_modified, is_test_history_in_tmp
from utils.file import actualize_test_history_in_tmp


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
    curses.curs_set(0)
    # refresh_main_screens(env)
    """ print hint for user """
    print_hint(env)

    if env.show_notes:
        show_notes(env)
    else:
        show_directory_content(env)
        if env.show_logs:
            show_logs(env)
    show_file_content(env)
    if env.show_tags:
        show_tags(env)

def rewrite_brows(env, hint=True):
    if hint:
        print_hint(env)
    show_directory_content(env)

def rewrite_file(env, hint=True):
    curses.curs_set(0)
    if hint:
        print_hint(env)
    show_file_content(env)
    if env.show_tags:
        show_tags(env)
    curses.curs_set(1)

def rewrite_notes(env, hint=True):
    if hint:
        print_hint(env)
    show_notes(env)


def print_hint(env):
    screen = env.screens.down
    screen.erase()
    screen.border(0)
    size = screen.getmaxyx()

    help_dict = env.control.get_hint_for_mode(env)
    if help_dict is not None:
        string = ""
        for key in help_dict:
            hint = " | " + str(key) + ":" + str(help_dict[key])
            if len(string) + len(hint) <= size[1]:
                string += hint
        screen.addstr(1, 1, string[2:])
    screen.refresh()


def print_help(screen, win, env, exit_mess, title, actions):
    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y

    screen.erase()
    screen.border(0)

    line = 1
    if exit_mess:
        if len(exit_mess) >= max_cols:
            exit_mess = exit_mess[:max_cols-1]
        screen.addstr(line, 1, exit_mess, curses.color_pair(COL_HELP))
        line += 1
    if title:
        if len(title) >= max_cols:
            title = title[:max_cols-1]
        screen.addstr(line, int(max_cols/2-len(title)/2)+1, title, curses.A_NORMAL)
        line += 1


    for idx, key in enumerate(actions):
        if idx < win.row_shift:
            continue
        if line >= max_rows:
            break

        # print key
        if len(key)+3 >= max_cols:
            break
        screen.addstr(line, 1, str(key), curses.color_pair(COL_HELP))

        # print action
        action = actions[key]
        free_space = max_cols-len(key)-3
        if len(action) > free_space:
            sublines = parse_line_into_sublines(action, free_space)
            for part in sublines:
                if line >= max_rows:
                    break
                screen.addstr(line, 3+len(key), str(part), curses.A_NORMAL)
                line +=1
        else:
            screen.addstr(line, 3+len(key), str(action), curses.A_NORMAL)
            line += 1
        screen.refresh()



def parse_line_into_sublines(line, max_cols):
    sublines = []

    # split string into list of words and spaces
    words = re.split(r'(\S+)', line)
    split_words = []
    for word in words:
        # if any single word is longer max free space, split it (otherwise it would never be printed)
        if len(word) >= max_cols:
            while len(word) >= max_cols:
                part = word[:max_cols-1]
                split_words.append(part)
                word = word[max_cols-1:]
        split_words.append(word)

    words = split_words
    while words:
        res_line = ""
        word = words[0] # get first word
        while len(res_line)+len(word) < max_cols: # check if the word fits in the line
            """ add word to the line """
            res_line += word
            del words[0]
            if not words:
                break
            word = words[0] # get next word
        # TODO !!!!!!! POZOR MOZE ROBIT BORDEL !!!!!!!
        res_line = res_line.strip()
        if res_line != "":
            sublines.append(res_line)
    return sublines



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
                save_buffer(stdscr, env)
                return True
            else:
                return False
    else:
        return True


def save_buffer(stdscr, env):
    if not env.file_to_open or not env.buffer:
        log("save buffer | missing env.file_to_open or mising env.buffer")
        return

    save_buffer_to_file(env.file_to_open, env.buffer)
    env.buffer.set_save_status(True)
    env.buffer.last_save = env.buffer.lines.copy()
    if env.report:
        save_report_to_file(env.report)

    # if buffer is test file, save test history
    if env.editing_test_file and env.cwd.proj:
        test_name = os.path.basename(os.path.dirname(env.file_to_open))
        if is_test_history_in_tmp(env.cwd.proj.path, test_name):
            """ print warning message """
            screen = env.screens.right
            screen.erase()
            screen.addstr(1, 1, str(TEST_MODIFICATION), curses.A_BOLD)
            screen.border(0)
            screen.refresh()

            key = stdscr.getch()
            if key == curses.KEY_F2: # save to history and actualize tmp
                history_test_modified(env.cwd.proj.path, test_name)
                env.tags = load_testcase_tags(os.path.dirname(env.file_to_open))
                actualize_test_history_in_tmp(env.cwd.proj.path, os.path.dirname(env.file_to_open))
            else: # dont save to history
                log("dont save old test version to history | will be discard after system exit")


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
    screen = env.screens.left_up if env.show_logs else env.screens.left
    win = env.windows.brows_up if env.show_logs else env.windows.brows

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y - 1

    """ print borders """
    screen.erase()
    if env.is_brows_mode():
        screen.attron(curses.color_pair(COL_BORDER))
        screen.border(0)
        screen.attroff(curses.color_pair(COL_BORDER))
    else:
        screen.border(0)

    # cwd = Directory(env.filter.root, files=env.filter.files) if env.filter_not_empty() else env.cwd
    cwd = env.cwd
    dirs, files = cwd.get_shifted_dirs_and_files(win.row_shift)


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

                if env.show_solution_info and cwd.dirs_info:
                    infos = None
                    if dir_name in cwd.dirs_info:
                        infos = cwd.dirs_info[dir_name]

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
    win = env.windows.view_up if env.show_tags else env.windows.view
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
            y = line_num-win.row_shift
            screen.addstr(y, 1+shift, line, text_color)

        screen.refresh()



""" view file content """
def show_file_content(env):
    screen = env.screens.right_up if env.show_tags else env.screens.right
    win = env.windows.view_up if env.show_tags else env.windows.view


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

                    # if cursor is on this line and col shift > 0 then start from col shift
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
            tags.data = dict(sorted(tags.data.items()))
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


def show_menu(screen, win, menu_options, env, keys=None, selected=None, color=None, title=None):
    screen.erase()
    screen.border(0)

    max_cols = win.end_x - win.begin_x - 1
    max_rows = win.end_y - win.begin_y - 1

    row = 0
    if title:
        screen.addstr(row+1, 1, title[:max_cols], color if color else curses.A_NORMAL)
        row += 1

    if selected is None:
        selected = []
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
                elif row+win.row_shift-1 in selected:
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


def show_logs(env):
    screen, win = env.screens.left_down, env.windows.logs

    # if env.user_logs_printed == env.user_logs and env.user_logs_printed_shift == win.row_shift:
        # return

    """ print borders """
    screen.erase()
    screen.border(0)
    if env.is_logs_mode():
        screen.attron(curses.color_pair(COL_BORDER))
        screen.border(0)
        screen.attroff(curses.color_pair(COL_BORDER))
    else:
        screen.border(0)

    max_cols = win.end_x - win.begin_x - 1
    max_rows = win.end_y - win.begin_y

    show_path(screen, "LOGS", max_cols)

    if not env.user_logs:
        screen.refresh()
        return

    try:
        line = 1
        for idx, item in enumerate(env.user_logs):
            if idx < win.row_shift:
                continue
            if line >= max_rows:
                break

            date, m_type, message = item
            date, m_type, message = str(date), str(m_type), str(message).strip()

            # set color according to message type
            if str(m_type).lower().strip() in ['e','error']:
                m_col = curses.color_pair(HL_RED)
            elif str(m_type).lower().strip() in ['i','info']:
                m_col = curses.A_NORMAL
            elif str(m_type).lower().strip() in ['w','warning']:
                m_col = curses.color_pair(HL_DARK_BLUE)
            else:
                m_col = curses.A_NORMAL

            data_to_print = [str(date), " | ", str(m_type), " | ", str(message)]
            data_colors = [curses.color_pair(HL_DARK_YELLOW), curses.A_NORMAL, m_col, curses.A_NORMAL, curses.A_NORMAL]
            x=1
            line_added = False
            for i, data in enumerate(data_to_print):
                col = data_colors[i]
                # print action
                free_space = max_cols-x
                if len(data) > free_space:
                    sublines = parse_line_into_sublines(data, free_space)
                    for part in sublines:
                        if line >= max_rows:
                            break
                        screen.addstr(line, x, str(part), col)
                        line +=1
                        line_added = True
                else:
                    screen.addstr(line, x, str(data), col)
                x += len(data)
            if not line_added:
                line += 1

        env.user_logs_printed = env.user_logs.copy()
        env.user_logs_printed_shift = win.row_shift

    except Exception as err:
        log("show logs | "+str(err)+" | "+str(traceback.format_exc()))
    finally:
        screen.refresh()

