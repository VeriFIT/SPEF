#!/usr/bin/env python3

import curses
import curses.ascii
import datetime
import json
import os
import re
import sys

from buffer import Buffer, Report, Tags, UserInput
from config import *
from directory import Directory
from window import Window, Cursor

ESC = 27

""" hladanie cesty projektu v ktorom su odovzdane riesenia
TODO: 1
-v aktualnej ceste buffer.file_name sa bude hladat cesta suboru s projektom
-hlada sa od definovaneho HOME az kym nenajde xlogin00 subor
-xlogin00 sa najde podla regexu x[a-z][a-z][a-z][a-z][a-z][0-9][0-9]
-teda z cesty HOME/.../.../xlogin00/dir/file bude subor projektu .../...

TODO: 2
-kazdy projekt bude nejak reprezentovany
-nazvy/cesty projektovych suborov budu niekde ulozene
-prehlada sa zoznam projektov
-skontroluje sa ci aktualna cesta buffer.file_name ma prefix zhodny s niektorym projektom
"""

HOME = "/home/naty/Others/ncurses/python"

# PROJ_DIR = "subject1/2021/project"
PROJ_DIR = "project"

LOG_FILE = f"{HOME}/framework/log"
TAG_DIR = f"{HOME}/framework/tags"
REPORT_DIR = f"{HOME}/framework/reports"

BORDER = 2
START_Y = 0
START_X = 0


def log(message):
    day = datetime.date.today()
    time = datetime.datetime.now().strftime("%X")
    with open(LOG_FILE, 'a') as f:
        f.write("{} {} | {}\n".format(day,time,message))

def preparation():
    """ clear log file """
    with open(LOG_FILE, 'w+'): pass

    """ create dirs for tags and reports """
    if not os.path.exists(TAG_DIR):
        os.makedirs(TAG_DIR)
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)


# browsing
B_HELP = {"F1":"help", "F2":"menu", "F3":"view/tag",
            "F4":"edit", "F5":"copy", "F6":"rename",
            "F8":"delete", "F9":"filter", "F10":"exit"}

# editing = is_view_mode + edit_allowed
E_HELP = {"F1":"help", "F2":"save", "F3":"view/tag",
            "F4":"note", "F5":"goto", "F8":"reload",
            "F9":"filter", "F10":"exit"}

"""
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


def print_hint(conf):
    screen = conf.down_screen
    screen.erase()
    screen.border(0)
    size = screen.getmaxyx()

    if conf.is_brows_mode():
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


def resize_all(stdscr, conf, force_resize=False):
    """ get cursor positions from old windows """
    l_win_old_row, l_win_old_col = conf.left_win.get_cursor_position()

    try:
        if curses.is_term_resized(curses.LINES,curses.COLS) or force_resize:
            """ screen resize """
            y,x = stdscr.getmaxyx()
            stdscr.clear()
            curses.resizeterm(y,x)
            stdscr.refresh()

            """ create screens with new size """
            screens, windows = create_screens_and_windows(y, x, conf.line_numbers)
            bkgd_col = curses.color_pair(2)
            conf = create_config(screens, windows, bkgd_col, conf)

            """ set new cursor positions to windows """
            l_win_new_row = min(l_win_old_row, conf.left_win.end_y-2)
            l_win_new_col = min(l_win_old_col, conf.left_win.end_x)
            conf.left_win.set_cursor(l_win_new_row, l_win_new_col)

            # TODO: cursor stays in the middle (see window resizing in vim)
            conf.right_win.set_cursor(conf.right_win.begin_y, conf.right_win.begin_x)

            """ rewrite all screens """
            print_hint(conf)
            show_directory_content(conf.left_screen, conf.left_win, conf.cwd, conf.highlight, conf.normal)
            if conf.edit_allowed:
                show_file_content(conf.right_screen, conf.right_win, conf.buffer, conf.report, conf)
            else:
                show_file_content(conf.right_up_screen, conf.right_up_win, conf.buffer, conf.report, conf)
                show_tags(conf.right_down_screen, conf.right_down_win, conf.tags)
    except Exception as err:
        log("resizing | "+str(err))
    finally:
        return conf


def create_screens_and_windows(height, width, line_numbers=None):
    half_width = int(width/2)
    d_win_lines = 1

    """ set window size and position """
    d_win_h, d_win_w = d_win_lines + BORDER, width - START_X
    l_win_h, l_win_w = height - d_win_h - START_Y, half_width
    r_win_h, r_win_w = height - d_win_h - START_Y, half_width - START_X

    d_win_y, d_win_x = START_Y + l_win_h, START_X
    l_win_y, l_win_x = START_Y, START_X
    r_win_y, r_win_x = START_Y, START_X + l_win_w

    left_screen = curses.newwin(l_win_h, l_win_w, l_win_y, l_win_x) # browsing
    right_screen = curses.newwin(r_win_h, r_win_w, r_win_y, r_win_x) # editing
    down_screen = curses.newwin(d_win_h, d_win_w, d_win_y, d_win_x) # hint

    right_up_h = int(r_win_h / 2) + int(r_win_h % 2 != 0)
    right_down_h = int(r_win_h / 2)

    right_up_screen = curses.newwin(right_up_h, r_win_w, r_win_y, r_win_x)
    right_down_screen = curses.newwin(right_down_h, r_win_w, r_win_y + right_up_h, r_win_x)

    if line_numbers is None:
        right_win = Window(r_win_h, r_win_w, r_win_y+1, r_win_x+1) # +1 stands for bordes at first line and col
        right_up_win = Window(right_up_h, r_win_w, r_win_y+1, r_win_x+1)
    else:
        shift = len(line_numbers)+1 # +1 stands for a space between line number and text
        right_win = Window(r_win_h, r_win_w-shift, r_win_y+1, r_win_x+1+shift) # +1 stands for bordes at first line and col
        right_up_win = Window(right_up_h, r_win_w-shift, r_win_y+1, r_win_x+1+shift)


    left_win = Window(l_win_h, l_win_w, 0, 0)
    right_down_win = Window(right_down_h, r_win_w, r_win_y+right_up_h+1, r_win_x+1)

    screens = {"LS":left_screen, "RS":right_screen, "DS":down_screen,
                "RUS":right_up_screen, "RDS":right_down_screen}
    windows = {"LW":left_win, "RW":right_win, 
                "RUW":right_up_win, "RDW":right_down_win}

    return screens, windows


def create_config(screens, windows, bkgd_col=None, config=None):
    if config:
        config.left_screen = screens["LS"]
        config.right_screen = screens["RS"]
        config.down_screen = screens["DS"]
    else:
        config = Config(screens["LS"], screens["RS"], screens["DS"])

    config.right_up_screen = screens["RUS"]
    config.right_down_screen = screens["RDS"]

    config.right_win = windows["RW"]
    config.left_win = windows["LW"]
    config.right_up_win = windows["RUW"]
    config.right_down_win = windows["RDW"]

    if bkgd_col:
        config.left_screen.bkgd(' ', bkgd_col)
        config.right_screen.bkgd(' ', bkgd_col)
        config.down_screen.bkgd(' ', bkgd_col)
        config.right_up_screen.bkgd(' ', bkgd_col)
        config.right_down_screen.bkgd(' ', bkgd_col)

    return config


def show_main_screens(stdscr, config):
    stdscr.erase()
    config.left_screen.border(0)
    config.right_screen.border(0)
    config.down_screen.border(0)

    stdscr.refresh()
    config.left_screen.refresh()
    config.right_screen.refresh()
    config.down_screen.refresh()


""" ======================= START MAIN ========================= """
def main(stdscr):
    log("START")
    stdscr.clear()
    curses.set_escdelay(1)

    """ set coloring """
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

    highlight = curses.color_pair(1)
    normal = curses.A_NORMAL
    bkgd_col = curses.color_pair(2)

    """ create screen for browsing, editing and showing hint """
    screens, windows = create_screens_and_windows(curses.LINES, curses.COLS)

    """ create config """
    config = create_config(screens, windows, bkgd_col=bkgd_col)
    config.left_win.set_cursor(0,0)
    config.set_coloring(highlight, normal)
    stdscr.bkgd(' ', bkgd_col)

    """ show all main screens """
    show_main_screens(stdscr, config)

    """ get current files and dirs """
    config.cwd = get_directory_content()

    while True:
        print_hint(config)
        if config.is_exit_mode():
            break
        elif config.is_brows_mode():
            config = directory_browsing(stdscr, config)
        elif config.is_view_mode():
            config = file_viewing(stdscr, config)
        elif config.is_tag_mode():
            config = tag_management(stdscr, config)

    log("END")
""" ======================= END MAIN ========================= """


""" **************************** START BROWSING **************************** """
def directory_browsing(stdscr, conf):
    curses.curs_set(0) # set cursor as invisible

    screen = conf.left_screen
    win = conf.left_win
    cwd = conf.cwd

    while True:
        """ print current directory structure """
        show_directory_content(screen, win, cwd, conf.highlight, conf.normal)

        key = stdscr.getch()
        try:
            # ======================= EXIT =======================
            if key in (curses.ascii.ESC, curses.KEY_F10): # if key F10 doesnt work, use alternative ALT+0
                conf.update_browsing_data(win, cwd) # save browsing state before exit browsing
                if file_changes_are_saved(stdscr, conf):
                    conf.set_exit_mode()
                    return conf
                else:
                    show_directory_content(screen, win, cwd, conf.highlight, conf.normal)
                    continue
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB: # ord('\t')
                conf.update_browsing_data(win, cwd)
                conf.set_view_mode()
                return conf
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(cwd, use_restrictions=False)
            elif key == curses.KEY_DOWN:
                win.down(cwd, use_restrictions=False)
            elif key == curses.KEY_RIGHT:
                if win.cursor.row < len(cwd.dirs):
                    """ go to subdirectory """
                    os.chdir(os.getcwd()+'/'+cwd.dirs[win.cursor.row])
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0) # set cursor on first position (first item)
            elif key == curses.KEY_LEFT:
                """ go to parent directory """
                current_dir = os.path.basename(os.getcwd()) # get directory name
                if current_dir: # if its not root
                    os.chdir('..')
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0)
                    """ set cursor position to prev directory """
                    dir_position = cwd.dirs.index(current_dir) # find position of prev directory
                    if dir_position:
                        for i in range(0, dir_position):
                            win.down(cwd, use_restrictions=False)
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen = conf.left_screen
                win = conf.left_win
            # ======================= F KEYS =======================
            elif key in (curses.KEY_F3, curses.KEY_F4):
                if win.cursor.row >= len(cwd.dirs):
                    conf.update_browsing_data(win, cwd)
                    dirs_and_files = cwd.get_all_items()
                    conf.file_to_open = os.getcwd()+'/'+dirs_and_files[win.cursor.row]
                    conf.set_view_mode()
                    """ F3: view/tag """
                    if key == curses.KEY_F3:
                        conf.disable_file_edit()
                        conf.right_up_win.reset_window()
                    """ F4: edit """
                    if key == curses.KEY_F4:
                        conf.enable_file_edit()
                        conf.right_win.reset_window()            
                    return conf
        except Exception as err:
            log("browsing | "+str(err))
            conf.set_exit_mode()
            return conf


def get_directory_content():
    path = os.getcwd() # current working directory
    files, dirs = [], []
    for (dir_path,dir_names,file_names) in os.walk(path):
        files.extend(file_names)
        dirs.extend(dir_names)
        break
    dirs.sort()
    files.sort()
    return Directory(path, dirs, files)

def show_directory_content(screen, win, cwd, highlight, normal):
    screen.erase()
    screen.border(0)

    shift = win.row_shift
    if shift > 0:
        dirs, files = cwd.get_shifted_dirs_and_files(shift)
    else:
        dirs = cwd.dirs
        files = cwd.files

    max_cols = win.end_x - win.begin_x
    try:
        """ show dir name """
        show_path(screen, cwd.path, max_cols)

        """ show dir content """
        if cwd.is_empty():
            screen.addstr(1, 1, "* This directory is empty *", normal | curses.A_BOLD)
        else:
            i=1
            for dir_name in dirs:
                if i > win.end_y - 1:
                    break
                coloring = (highlight if i+shift == win.cursor.row+1 else normal)
                screen.addstr(i, 1, "/"+str(dir_name[:max_cols-2]), coloring | curses.A_BOLD)
                i+=1
            for file_name in files:
                if i > win.end_y - 1:
                    break
                coloring = highlight if i+shift == win.cursor.row+1 else normal
                screen.addstr(i, 1, str(file_name[:max_cols-1]), coloring)
                i+=1
    except Exception as err:
        log("show directory | "+str(err))
    finally:
        screen.refresh()

def show_path(screen, path, max_cols):
    while len(path) > max_cols-2:
        path = path.split(os.sep)[1:]
        path = "/".join(path)
    dir_name = str(path)
    screen.addstr(0, int(max_cols/2-len(dir_name)/2), dir_name)
    screen.refresh()

""" **************************** END BROWSING **************************** """



EXIT_WITHOUT_SAVING_MESSAGE = """WARNING: Exit without saving.\n\
    Press F2 to save and exit.\n\
    Press {} to force exiting without saving.\n\
    Press any other key to continue editing your file."""

RELOAD_FILE_WITHOUT_SAVING = """WARNING: Reload file will discard changes.\n\
    Press F2 to save changes.\n\
    Press {} or Enter to reload file and discard all changes.\n\
    Press any other key to continue editing your file."""

""" check if file changes are saved or user want to save or discard them """
def file_changes_are_saved(stdscr, conf, warning=None, exit_key=None):
    if conf.buffer:
        if (conf.buffer.is_saved) or (conf.buffer.original_buff == conf.buffer.lines):
            return True
        else:
            curses_key, str_key = exit_key if exit_key else (ESC, "ESC")
            message = warning if warning else EXIT_WITHOUT_SAVING_MESSAGE
            """ print warning message """
            screen = conf.right_screen
            screen.erase()
            screen.addstr(1, 1, str(message.format(str_key)), curses.A_BOLD)
            screen.border(0)
            screen.refresh()

            key = stdscr.getch()
            if key == curses_key: # force exit without saving
                return True
            elif key == curses.KEY_F2: # save and exit
                save_buffer(conf.file_to_open, conf.buffer, conf.report)
                return True
            else:
                return False
    else:
        return True


""" **************************** START VIEWING **************************** """
def file_viewing(stdscr, conf):
    curses.curs_set(1) # set cursor as visible

    screen = conf.right_screen if conf.edit_allowed else conf.right_up_screen
    win = conf.right_win if conf.edit_allowed else conf.right_up_win

    if not conf.file_to_open: # there is no file to open and edit
        conf.set_brows_mode()
        return conf
    file_already_loaded = False
    report_already_loaded = False

    """ try load file content to buffer """
    if conf.buffer and conf.buffer.path == conf.file_to_open:
        file_already_loaded = True
        buffer = conf.buffer
    else:
        try:
            with open(conf.file_to_open, 'r') as f:
                lines = f.read().splitlines()
            buffer = Buffer(conf.file_to_open, lines)
            conf.buffer = buffer
        except Exception as err:
            log("load file content | "+str(err))
            conf.set_exit_mode()
            return conf

    """ try load file tags to config - only for view, tags will not change """
    if not conf.edit_allowed and (not conf.tags or not file_already_loaded): # tag file wasnt loaded yet
        file_name = os.path.basename(conf.file_to_open)
        tag_path = os.path.join(TAG_DIR, str(file_name))
        tag_file = os.path.splitext(tag_path)[0]+".json"
        try:
            with open(tag_file, 'r') as f:
                data = json.load(f)
            conf.tags = Tags(tag_file, data)
        except json.decoder.JSONDecodeError:
            conf.tags = Tags(tag_file, {})
        except FileNotFoundError:
            conf.tags = Tags(tag_file, {})
        except Exception as err:
            log("load file tags | "+str(err))
            conf.set_exit_mode()
            return conf

    """ try load code review to report  """
    conf.note_highlight = False
    report = None
    if buffer.path.startswith(HOME): # opened file is some file from students projects
        # TODO: get project directory
        project = PROJ_DIR
        file_login = os.path.relpath(buffer.path, f"{HOME}/{project}").split(os.sep)[0]
        login_match = bool(re.match("x[a-z]{5}[0-9]{2}", file_login))
        if login_match:
            conf.note_highlight = True
            if conf.report:
                # check if loaded report is related to opened file in buffer
                report_login = os.path.relpath(conf.report.path, f"{REPORT_DIR}/{project}").split(os.sep)[0]
                if report_login == file_login:
                    report_already_loaded = True
                    report = conf.report
            if not conf.report or not report_already_loaded:
                # try get report for file in buffer
                try:
                    report = get_report_for_file(project, file_login)
                    conf.report = report
                except Exception as err:
                    log("load file report | "+str(err))
                    conf.set_exit_mode()
                    return conf

    note_entering = False
    user_input = UserInput()

    """ calculate line numbers """
    if conf.line_numbers:
        conf.enable_line_numbers(buffer)
        resize_all(stdscr, conf, True)


    while True:
        try:
            """ print current file content and move cursor to correct position """
            show_file_content(screen, win, buffer, report, conf, user_input if note_entering else None)
            if not conf.edit_allowed:
                show_tags(conf.right_down_screen, conf.right_down_win, conf.tags)

            if note_entering:
                shifted_pointer = user_input.get_shifted_pointer()
                new_col = win.begin_x + shifted_pointer
                new_row = win.end_y-2
                stdscr.move(new_row, new_col)
            else:
                new_row, new_col = win.get_cursor_position()
                stdscr.move(new_row, new_col)
        except Exception as err:
            log("viewing print file | "+str(err))
            conf.set_exit_mode()
            return conf

        key = stdscr.getch()

        # ======================= NOTE INPUT =======================
        if note_entering:
            if key in (curses.ascii.ESC, curses.KEY_F10): # exit note input
                note_entering = False
                user_input.reset()
            elif key == curses.KEY_LEFT:
                user_input.left(win)
            elif key == curses.KEY_RIGHT:
                user_input.right(win)
            elif key == curses.KEY_DC:
                user_input.delete_symbol(win)
            elif key == curses.KEY_BACKSPACE:
                user_input.left(win)
                user_input.delete_symbol(win)
            elif key == curses.ascii.NL:
                text = ''.join(user_input.text)
                file_name = os.path.basename(buffer.path)
                report.add_note(file_name, win.cursor.row-1, win.cursor.col-win.begin_x, text)
                note_entering = False
                user_input.reset()
            elif curses.ascii.isprint(key):
                user_input.insert_symbol(win, chr(key))
            continue


        try:
            # ======================= EXIT =======================
            if key in (curses.ascii.ESC, curses.KEY_F10): # curses.ascii.ESC
                conf.update_viewing_data(win, buffer, report)
                if file_changes_are_saved(stdscr, conf):
                    conf.set_exit_mode()
                    return conf
                else:
                    # show_file_content(screen, win, buffer, report, conf)
                    continue
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB: # ord('\t')
                conf.update_viewing_data(win, buffer, report)
                if conf.edit_allowed:
                    if file_changes_are_saved(stdscr, conf):
                        conf.set_brows_mode()
                    show_file_content(screen, win, buffer, report, conf)
                    return conf
                else:
                    conf.set_tag_mode()
                    return conf
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(buffer, use_restrictions=True)
            elif key == curses.KEY_DOWN:
                win.down(buffer, use_restrictions=True)
            elif key == curses.KEY_LEFT:
                win.left(buffer)
            elif key == curses.KEY_RIGHT:
                win.right(buffer)
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen = conf.right_screen if conf.edit_allowed else conf.right_up_screen
                win = conf.right_win if conf.edit_allowed else conf.right_up_win
            else:
                # ***************************** E.D.I.T *****************************
                if conf.edit_allowed:
                    # ======================= EDIT FILE =======================
                    if key == curses.KEY_DC: # \x04 for MacOS which doesnt correctly decode delete key
                        report = buffer.delete(win, report)
                    elif key == curses.KEY_BACKSPACE: # \x7f for MacOS
                        if (win.cursor.row, win.cursor.col) > (win.begin_y, win.begin_x):
                            win.left(buffer)
                            report = buffer.delete(win, report)
                    elif key == curses.ascii.NL: # ord('\n')
                        report = buffer.newline(win, report)
                        win.right(buffer)
                    elif curses.ascii.isprint(key):
                        buffer.insert(win, chr(key))
                        win.right(buffer)
                        # for _ in str_key:
                            # win.right(buffer)
                    # ======================= F KEYS =======================
                    elif key == curses.KEY_F2:
                        """ F2: save file """
                        save_buffer(conf.file_to_open, buffer, report)
                    elif key == curses.KEY_F3:
                        """ F3: view/tag """
                        conf.update_viewing_data(win, buffer, report)
                        if file_changes_are_saved(stdscr, conf):
                            conf.disable_file_edit()
                            return conf
                        else:
                            show_file_content(screen, win, buffer, report, conf)
                    elif key == curses.KEY_F4:
                        """ F4: note """
                        if report:
                            note_entering = True
                            # text = stdscr.getstr(win.end_y-win.begin_y, win.begin_x).decode(encoding="utf-8")
                            # file_name = os.path.basename(buffer.path)
                            # report.add_note(file_name, win.cursor.row-1, win.cursor.col-win.begin_x, text)

                    elif key == curses.KEY_F8:
                        """ F8: reload from last save """
                        conf.update_viewing_data(win, buffer, report)
                        exit_key = (curses.KEY_F8, "F8")
                        if file_changes_are_saved(stdscr, conf, RELOAD_FILE_WITHOUT_SAVING, exit_key):
                            buffer.lines = buffer.last_save.copy()
                            if report:
                                report.code_review = report.last_save.copy()
                    # ======================= CTRL KEYS =======================
                    elif curses.ascii.ismeta(key):
                        """ CTRL + UP / CTRL + DOWN """
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '7' or hex(key) == "0x237": # CTRL + UP
                            if report and conf.note_highlight:
                                file_name = os.path.basename(buffer.path)
                                prev_note = report.get_prev_line_with_note(file_name, win.cursor.row-1)
                                if prev_note:
                                    y,x,_ = prev_note
                                    while win.cursor.row != y:
                                        win.up(buffer, use_restrictions=True)

                        if ctrl_key == '^N' or hex(key) == "0x20e": # CTRL + DOWN
                            if report and conf.note_highlight:
                                file_name = os.path.basename(buffer.path)
                                next_note = report.get_next_line_with_note(file_name, win.cursor.row)
                                if next_note:
                                    y,x,_ = next_note
                                    while win.cursor.row != y:
                                        win.down(buffer, use_restrictions=True)

                    elif curses.ascii.iscntrl(key):
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '^L':
                            """ CTRL + L reaload from original buff """
                            buffer.lines = buffer.original_buff.copy()
                            if report:
                                report.code_review = report.original_report.copy()
                        elif ctrl_key == '^N':
                            """ CTRL + N enable/disable line numbers """
                            if conf.line_numbers:
                                conf.disable_line_numbers()
                            else:
                                conf.enable_line_numbers(buffer)
                            resize_all(stdscr, conf, True)
                        elif ctrl_key == '^H':
                            """ CTRL + H enable/disable note highlight """
                            conf.note_highlight = not conf.note_highlight
                        elif ctrl_key == '^R':
                            """ CTRL + R remove notes on current line """
                            if report:
                                file_name = os.path.basename(buffer.path)
                                report.delete_notes_on_line(file_name, win.cursor.row-1)
                        elif ctrl_key == '^E': # !!!!!!!!!!!!!! TODO : note management / note editing  in separate window !!!!!!!!!!!!!!!!!!!!!
                            """ CTRL + E edit note """
                            if report:
                                file_name = os.path.basename(buffer.path)
                                line_notes = report.get_notes_on_line(file_name, win.cursor.row-1)
                                if len(line_notes) == 1:
                                    # open note for edit
                                    y, x, text = line_notes[0]
                                    report.delete_note(file_name, y, x)
                                    user_input.text = list(text)
                                    note_entering = True
                                elif len(line_notes) > 1:
                                    # choose which note you want to edit
                                    log(len(line_notes))
                                    pass
                # ***************************** E.D.I.T *****************************
                # ************************* V.I.E.W / T.A.G *************************
                else:
                    # ======================= F KEYS =======================
                    if key == curses.KEY_F2:
                        pass # TODO F2: ???
                    elif key == curses.KEY_F3:
                        pass # TODO F3: ???
                    elif key == curses.KEY_F4:
                        """ F4: edit """
                        conf.enable_file_edit()
                        return conf
                    elif key == curses.KEY_F8:
                        pass # TODO F8: ???
                    # ======================= CTRL KEYS =======================
                    elif curses.ascii.iscntrl(key):
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '^N':
                            """ CTRL + N enable/disable line numbers """
                            if conf.line_numbers:
                                conf.disable_line_numbers()
                            else:
                                conf.enable_line_numbers(buffer)
                            resize_all(stdscr, conf, True)
                # ************************* V.I.E.W / T.A.G *************************
        except Exception as err:
            log("viewing Exception | "+str(err))
            conf.set_exit_mode()
            return conf


def save_buffer(file_name, buffer, report=None):
    with open(file_name, 'w') as f:
        lines = '\n'.join(buffer.lines)
        f.write(lines)
    buffer.set_save_status(True)
    buffer.last_save = buffer.lines.copy()
    if report:
        notes = report_to_str(report.code_review)
        with open(report.path, 'w+') as f:
            f.write(notes)
        report.last_save = report.code_review.copy()


def show_file_content(screen, win, buffer, report, conf, user_input=None):
    screen.erase()
    screen.border(0)
    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y
    last_row = win.end_y-win.begin_y-1

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
        show_path(screen, buffer.path, max_cols+ (shift if conf.line_numbers else 1))

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


def get_report_for_file(project, file_login):
    report_path = f"{REPORT_DIR}/{project}/{file_login}"
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            lines = f.read()
        code_review = str_to_report(lines)
        return Report(report_path, code_review)
    else:
        # there is no report yet for this project/login
        return Report(report_path, {})


def str_to_report(full_text):
    code_review = {}
    text = None
    line_content = "INFO"
    for line in full_text.split("\n"):
        if line == "":
            if line_content == "NOTE":
                note = (int(row), int(col), text)
                if file_name in code_review:
                    code_review[file_name].append(note)
                else:
                    code_review[file_name] = [note]
            line_content = "INFO"
            continue
        if line_content == "INFO":
            note = line.split(":")
            if len(note) != 3:
                log("invalid code_review syntax")
                raise Exception("invalid code_review syntax")
            file_name, row, col = note
            text = None
            line_content = "NOTE"
        elif line_content == "NOTE":
            text = f"{text}\n{line}" if text else line
    return code_review

def report_to_str(code_review):
    str_rep = ""
    for file_name in code_review:
        notes = code_review[file_name]
        for note in notes:
            str_rep += "{}:{}:{}\n{}\n\n".format(file_name, *note)
    return str_rep



""" **************************** END VIEWING **************************** """


""" **************************** START TAGGING **************************** """
def tag_management(stdscr, conf):
    curses.curs_set(1)

    screen = conf.right_down_screen
    win = conf.right_down_win

    """ read tags from file """
    file_name = os.path.basename(conf.file_to_open)
    tag_path = os.path.join(TAG_DIR, str(file_name))
    tag_file = os.path.splitext(tag_path)[0]+".json"
    try:
        if conf.tags: # tag file was already loaded
            tags = conf.tags
        else:
            with open(tag_file, 'r') as f:
                data = json.load(f)
            tags = Tags(tag_file, data)
            conf.tags = tags
    except json.decoder.JSONDecodeError:
        tags = Tags(tag_file, {})
        conf.tags = tags
    except FileNotFoundError:
        tags = Tags(tag_file, {})
        conf.tags = tags
    except Exception as err:
        log("tagging | "+str(err))
        conf.set_exit_mode()
        return conf

    user_input = []
    pointer = 0

    while True:
        show_tags(screen, win, tags, user_input)

        row, col = win.end_y-2, win.begin_x
        stdscr.move(row, col+pointer)

        key = stdscr.getch()
        try:
            # ======================= EXIT =======================
            if key in (curses.ascii.ESC, curses.KEY_F10): # curses.ascii.ESC
                tags.save_to_file()
                conf.update_tagging_data(win, tags)
                conf.set_exit_mode()
                return conf
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                tags.save_to_file()
                conf.update_tagging_data(win, tags)
                conf.set_brows_mode()
                return conf
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen = conf.right_down_screen
                win = conf.right_down_win
            # ======================= ARROWS =======================
            elif key == curses.KEY_LEFT:
                if pointer > 0:
                    pointer -= 1
            elif key == curses.KEY_RIGHT:
                if pointer < len(user_input):
                    pointer += 1
            # ======================= INPUT =======================
            elif key == curses.KEY_DC:
                if pointer < len(user_input):
                    del user_input[pointer]
            elif key == curses.KEY_BACKSPACE:
                if pointer > 0:
                    pointer -= 1
                    if pointer < len(user_input):
                        del user_input[pointer]
            elif key == curses.ascii.NL:
                command_parts = ''.join(user_input).split()
                if len(command_parts) < 2:
                    log("unknown command, press F1 to see help")
                else:
                    command, tag_name, *args = command_parts
                    if command == "set":
                        tags.set_tag(tag_name, args)
                    elif command == "remove":
                        tags.remove_tag(tag_name)
                    else:
                        # TODO: unknown command, press F1 to see how to use command line utility for tag management
                        log("unknown command, press F1 to see help")
                tags.save_to_file()
                user_input = []
                pointer = 0
            elif curses.ascii.isprint(key):
                user_input.insert(pointer, chr(key))
                pointer += 1
            # ======================= F KEYS =======================
            elif key == curses.KEY_F4:
                """ F4: edit """
                conf.update_tagging_data(win, tags)
                conf.file_to_open = tags.path
                conf.set_view_mode()
                conf.enable_file_edit()
                conf.right_win.reset_window()
                return conf
        except Exception as err:
            log("tagging | "+str(err))
            conf.set_exit_mode()
            return conf


def show_tags(screen, win, tags, command=None):
    screen.erase()
    screen.border(0)

    last_row = win.end_y-win.begin_y-1
    max_cols = win.end_x - win.begin_x
    try:
        """ show file name """
        show_path(screen, tags.path, max_cols)

        """ show tags """
        if tags.data:
            for row, name in enumerate(tags.data):
                if row+2 > last_row:
                    break
                params = tags.data[name]
                str_params = "(" + ",".join(map(str,params)) + ")"
                line = "#"+str(name)+str_params
                if len(line) > max_cols:
                    line = line[:max_cols - 1]
                screen.addstr(row+1, 1, line)
    except Exception as err:
        log("show tags | "+str(err))
    finally:
        screen.refresh()

    if command:
        command_str = ''.join(command)
        screen.addstr(last_row, 1, command_str)
        screen.refresh()


""" **************************** END TAGGING **************************** """


if __name__ == "__main__":
    preparation()

    stdscr = curses.initscr()
    stdscr.keypad(True) # enable read special keys
    curses.wrapper(main)
    curses.endwin()
