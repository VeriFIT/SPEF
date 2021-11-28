#!/usr/bin/env python3

import curses
import curses.ascii
import datetime
import json
import yaml
import os
import re
import sys
import fnmatch
import glob


from buffer import Buffer, Report, Tags, UserInput
from config import Config
from directory import Directory, Filter
from window import Window, Cursor
from printing import *
from logger import *
from coloring import *


ESC = 27

SOLUTION_IDENTIFIER = "x[a-z]{5}[0-9]{2}"

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


# PROJ_DIR = "subject1/2021/project"
# PROJ_DIR = "project"



def preparation():
    """ clear log file """
    with open(LOG_FILE, 'w+'): pass

    """ create dirs for tags and reports """
    if not os.path.exists(TAG_DIR):
        os.makedirs(TAG_DIR)
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)


def resize_all(stdscr, conf, force_resize=False):
    """ get cursor positions from old windows """
    l_win_old_row, l_win_old_col = conf.left_win.get_cursor_position()

    result_conf = conf
    try:
        if curses.is_term_resized(curses.LINES,curses.COLS) or force_resize:
            """ screen resize """
            y,x = stdscr.getmaxyx()
            stdscr.clear()
            curses.resizeterm(y,x)
            stdscr.refresh()

            """ create screens with new size """
            screens, windows = create_screens_and_windows(y, x, conf.line_numbers)
            new_conf = create_config(screens, windows, conf)

            """ set new cursor positions to windows """
            l_win_new_row = min(l_win_old_row, new_conf.left_win.end_y-2)
            l_win_new_col = min(l_win_old_col, new_conf.left_win.end_x)
            new_conf.left_win.set_cursor(l_win_new_row, l_win_new_col)

            # TODO: cursor stays in the middle (see window resizing in vim)
            new_conf.right_win.set_cursor(new_conf.right_win.begin_y, new_conf.right_win.begin_x)

            """ rewrite all screens """
            print_hint(new_conf)
            show_directory_content(new_conf.left_screen, new_conf.left_win, new_conf.cwd, new_conf)
            if new_conf.edit_allowed:
                show_file_content(new_conf.right_screen, new_conf.right_win, new_conf.buffer, new_conf.report, new_conf)
            else:
                show_file_content(new_conf.right_up_screen, new_conf.right_up_win, new_conf.buffer, new_conf.report, new_conf)
                show_tags(new_conf.right_down_screen, new_conf.right_down_win, new_conf.tags, new_conf)
            result_conf = new_conf
    except Exception as err:
        log("resizing | "+str(err))
    finally:
        return result_conf


def create_screens_and_windows(height, width, line_numbers=None):
    half_width = int(width/2)
    d_win_lines = 1

    """ set window size and position """
    d_win_h, d_win_w = d_win_lines + 2, width # 2 stands for borders
    l_win_h, l_win_w = height - d_win_h , half_width
    r_win_h, r_win_w = height - d_win_h , half_width

    d_win_y, d_win_x = l_win_h, 0
    l_win_y, l_win_x = 0, 0
    r_win_y, r_win_x = 0, l_win_w

    left_screen = curses.newwin(l_win_h, l_win_w, l_win_y, l_win_x) # browsing
    right_screen = curses.newwin(r_win_h, r_win_w, r_win_y, r_win_x) # editing
    down_screen = curses.newwin(d_win_h, d_win_w, d_win_y, d_win_x) # hint

    right_up_h = int(r_win_h / 2) + int(r_win_h % 2 != 0)
    right_down_h = int(r_win_h / 2)

    right_up_screen = curses.newwin(right_up_h, r_win_w, r_win_y, r_win_x)
    right_down_screen = curses.newwin(right_down_h, r_win_w, r_win_y + right_up_h, r_win_x)

    if line_numbers is None:
        right_win = Window(r_win_h, r_win_w, r_win_y, r_win_x, border=1) # +1 stands for bordes at first line and col
        right_up_win = Window(right_up_h, r_win_w, r_win_y, r_win_x, border=1)
    else:
        shift = len(line_numbers)+1 # +1 stands for a space between line number and text
        right_win = Window(r_win_h, r_win_w-shift, r_win_y, r_win_x+shift, border=1, line_num_shift=shift) # +1 stands for bordes at first line and col
        right_up_win = Window(right_up_h, r_win_w-shift, r_win_y, r_win_x+shift, border=1, line_num_shift=shift)


    left_win = Window(l_win_h, l_win_w, l_win_y, l_win_x)
    right_down_win = Window(right_down_h, r_win_w, r_win_y+right_up_h, r_win_x, border=1)

    screens = {"LS":left_screen, "RS":right_screen, "DS":down_screen,
                "RUS":right_up_screen, "RDS":right_down_screen}
    windows = {"LW":left_win, "RW":right_win, 
                "RUW":right_up_win, "RDW":right_down_win}

    return screens, windows

def resize_win(win, line_numbers):
    new_shift = len(line_numbers)+1

    shift = win.line_num_shift
    border = win.border
    begin_y = win.begin_y - win.border
    begin_x = win.begin_x - win.border - shift
    height = win.end_y - win.begin_y + 1
    width = win.end_x - win.begin_x + 1 + shift

    win = Window(height, width-new_shift, begin_y, begin_x+new_shift, border=border, line_num_shift=new_shift)
    return win


def create_config(screens, windows, config=None):
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

    bkgd_col = curses.color_pair(BKGD)
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
    curses.use_default_colors()

    init_color_pairs()
    bkgd_color = curses.color_pair(BKGD)

    """ create screen for browsing, editing and showing hint """
    screens, windows = create_screens_and_windows(curses.LINES, curses.COLS)

    """ create config """
    config = create_config(screens, windows)
    config.left_win.set_cursor(0,0)
    stdscr.bkgd(' ', bkgd_color)

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


def filter_management(stdscr, screen, win, user_input, conf):
    curses.curs_set(1)

    if not user_input:
        user_input = UserInput()

    if not conf.filter:
        project_path = conf.get_project_path()
        conf.filter = Filter(project_path)

    print_hint(conf, filter_mode=True)

    while True:
        try:

            """ show user input """
            max_cols = win.end_x - win.begin_x
            max_rows = win.end_y - win.begin_y - 1
            show_user_input(screen, user_input, max_rows, max_cols, conf)

            shifted_pointer = user_input.get_shifted_pointer()
            new_row, new_col = win.last_row, win.begin_x+1-win.border+shifted_pointer
            if conf.line_numbers and conf.is_view_mode():
                new_col -= win.line_num_shift
            stdscr.move(new_row, new_col)


            key = stdscr.getch()

            if key in (curses.ascii.ESC, curses.KEY_F10): # exit filter management
                user_input.reset()
                curses.curs_set(0)
                return conf
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen, win = conf.get_screen_for_current_mode()
            elif key == curses.KEY_F8: # remove all filters
                # conf.filter.reset_by_current_mode(conf)
                conf.filter.reset_all()
                conf.filter.find_files(conf)
                conf.cwd = get_directory_content()
                user_input.reset()
                curses.curs_set(0)
                return conf
            # ============ edit user input ============
            elif key == curses.KEY_LEFT:
                user_input.left(win)
            elif key == curses.KEY_RIGHT:
                user_input.right(win)
            elif key == curses.KEY_DOWN:
                end_of_input = len(user_input)
                user_input.pointer = end_of_input
                user_input.horizontal_shift(win)
            elif key == curses.KEY_UP:
                user_input.pointer = 0
                user_input.col_shift = 0
            elif key == curses.KEY_DC:
                user_input.delete_symbol(win)
            elif key == curses.KEY_BACKSPACE:
                if user_input.pointer > 0:
                    user_input.left(win)
                    user_input.delete_symbol(win)
            elif curses.ascii.isprint(key):
                user_input.insert_symbol(win, chr(key))
            elif key == curses.ascii.NL: # enter filter
                text = ''.join(user_input.text)
                conf.filter.add_by_current_mode(conf, text)
                conf.filter.find_files(conf)
                user_input.reset()
                curses.curs_set(0)
                return conf
        except Exception as err:
            log("filter management | "+str(err))
            conf.set_exit_mode()
            return conf


""" **************************** START BROWSING **************************** """
def directory_browsing(stdscr, conf):
    curses.curs_set(0)

    screen = conf.left_screen
    win = conf.left_win

    cwd = Directory(conf.filter.project_path, files=conf.filter.files) if conf.filter_not_empty() else conf.cwd

    while True:
        show_directory_content(screen, win, cwd, conf)

        # show file buffer and tags if quick view is on
        if conf.quick_view:
            idx = win.cursor.row
            if idx >= len(cwd.dirs) and idx < len(cwd):
                dirs_and_files = cwd.get_all_items()
                conf.set_file_to_open(os.path.join(cwd.path, dirs_and_files[idx]))
                new_conf, buffer, succ = load_buffer_and_tags(conf)
                if not succ: # couldnt load buffer and/or fags for current file
                    conf.set_file_to_open(None)
                    conf.set_brows_mode()
                else:
                    """ calculate line numbers """
                    if conf.line_numbers:
                        new_conf.enable_line_numbers(buffer)
                        new_conf.right_up_win = resize_win(new_conf.right_up_win, new_conf.line_numbers)
                    conf = new_conf
                    show_file_content(conf.right_up_screen, conf.right_up_win, buffer, None, conf, None)
                    show_tags(conf.right_down_screen, conf.right_down_win, conf.tags, conf)
            else:
                conf.set_file_to_open(None)


        key = stdscr.getch()

        try:
            # ======================= EXIT =======================
            if key == curses.KEY_F10: # if key F10 doesnt work, use alternative ALT+0
                conf.update_browsing_data(win, cwd) # save browsing state before exit browsing
                if file_changes_are_saved(stdscr, conf):
                    conf.set_exit_mode()
                    return conf
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                conf.update_browsing_data(win, cwd)
                conf.set_view_mode()                    
                return conf
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(cwd, use_restrictions=False)
            elif key == curses.KEY_DOWN:
                win.down(cwd, filter_on=conf.path_filter_on(), use_restrictions=False)
            elif key == curses.KEY_RIGHT:
                idx = win.cursor.row
                if not conf.filter_not_empty() and idx < len(cwd.dirs):
                    """ go to subdirectory """
                    os.chdir(os.path.join(cwd.path, cwd.dirs[idx]))
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0) # set cursor on first position (first item)
            elif key == curses.KEY_LEFT:
                current_dir = os.path.basename(cwd.path) # get directory name
                if not conf.filter_not_empty() and current_dir: # if its not root
                    """ go to parent directory """
                    os.chdir('..')
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0)
                    """ set cursor position to prev directory """
                    dir_position = cwd.dirs.index(current_dir) # find position of prev directory
                    if dir_position:
                        for i in range(0, dir_position):
                            win.down(cwd, filter_on=conf.path_filter_on(), use_restrictions=False)
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen, win = conf.left_screen, conf.left_win
            # ======================= F KEYS =======================
            elif key == curses.KEY_F4:
                idx = win.cursor.row
                if idx >= len(cwd.dirs) or conf.filter: # cant open direcotry
                    conf.update_browsing_data(win, cwd)
                    dirs_and_files = cwd.get_all_items()
                    conf.enable_file_edit()
                    conf.set_file_to_open(os.path.join(cwd.path, dirs_and_files[idx]))
                    conf.set_view_mode()
                    return conf
            elif key == curses.KEY_F3:
                conf.update_browsing_data(win, cwd)
                conf.quick_view = not conf.quick_view
                conf.right_up_win.reset()
                conf.right_down_win.reset()
                conf.right_up_screen.erase()
                conf.right_up_screen.border(0)
                conf.right_down_screen.erase()
                conf.right_down_screen.border(0)
            elif key == curses.KEY_F9: # set filter
                user_input = UserInput()
                if conf.path_filter_on():
                    user_input.text = list(conf.filter.path)
                conf = filter_management(stdscr, screen, win, user_input, conf)
                if conf.is_exit_mode():
                    return conf
                screen, win = conf.left_screen, conf.left_win
                # actualize current working directory according to filter
                if conf.filter_not_empty():
                    cwd = Directory(conf.filter.project_path, files=conf.filter.files)
                else:
                    cwd = conf.cwd
                win.reset_shifts()
                win.set_cursor(0,0)
        except Exception as err:
            log("browsing with quick view | "+str(err))
            conf.set_exit_mode()
            return conf



def get_directory_content():
    path = os.getcwd() # current working directory
    files, dirs = [], []
    for dir_path, dir_names, file_names in os.walk(path):
        files.extend(file_names)
        dirs.extend(dir_names)
        break
    dirs.sort()
    files.sort()
    return Directory(path, dirs, files)


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


    """ try load file content and tags """
    conf, buffer, succ = load_buffer_and_tags(conf)
    if not succ:
        return conf


    """ try load code review to report  """
    report_already_loaded = False
    conf.note_highlight = False
    report = None
    if buffer.path.startswith(HOME): # opened file is some file from students projects
        project_path = conf.get_project_path()
        file_login = os.path.relpath(buffer.path, project_path).split(os.sep)[0]
        report_file = get_report_file_name(buffer.path)
        login_match = bool(re.match(SOLUTION_IDENTIFIER, file_login))
        if login_match:
            conf.note_highlight = True
            if conf.report:
                if conf.report.path == report_file:
                    report_already_loaded = True
                    report = conf.report
            if not conf.report or not report_already_loaded:
                # try get report for file in buffer
                try:
                    report = load_report_from_file(buffer.path)
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
        conf = resize_all(stdscr, conf, True)
        win = conf.right_win if conf.edit_allowed else conf.right_up_win


    while True:
        """ print current file content """
        show_file_content(screen, win, buffer, report, conf, user_input if note_entering else None)
        if not conf.edit_allowed and conf.tags:
            show_tags(conf.right_down_screen, conf.right_down_win, conf.tags, conf)

        try:
            """ move cursor to correct position """
            if note_entering:
                shifted_pointer = user_input.get_shifted_pointer()
                new_row, new_col = win.last_row, win.begin_x+1-win.border+shifted_pointer
                if conf.line_numbers:
                    new_col -= win.line_num_shift
                stdscr.move(new_row, new_col)
            else:
                new_row, new_col = win.get_cursor_position()
                stdscr.move(new_row, new_col)
        except Exception as err:
            log("move cursor | "+str(err))
            conf.set_exit_mode()
            return conf

        key = stdscr.getch()

        # ======================= USER INPUT =======================
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
                if user_input.pointer > 0:
                    user_input.left(win)
                    user_input.delete_symbol(win)
            elif key == curses.ascii.NL:
                text = ''.join(user_input.text)
                report.add_note(win.cursor.row, win.cursor.col-win.begin_x, text)
                note_entering = False
                user_input.reset()
            elif curses.ascii.isprint(key):
                user_input.insert_symbol(win, chr(key))
            continue

        try:
            # ======================= EXIT =======================
            if key == curses.KEY_F10:
                conf.update_viewing_data(win, buffer, report)
                if file_changes_are_saved(stdscr, conf):
                    conf.set_exit_mode()
                    return conf
                else:
                    continue
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
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
                win.down(buffer, filter_on=conf.content_filter_on(), use_restrictions=True)
            elif key == curses.KEY_LEFT:
                win.left(buffer)
            elif key == curses.KEY_RIGHT:
                win.right(buffer, filter_on=conf.content_filter_on())
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
                    elif key == curses.ascii.NL:
                        report = buffer.newline(win, report)
                        win.right(buffer, filter_on=conf.content_filter_on())
                    elif curses.ascii.isprint(key):
                        buffer.insert(win, chr(key))
                        win.right(buffer, filter_on=conf.content_filter_on())
                    # ======================= F KEYS =======================
                    elif key == curses.KEY_F2: # save file
                        save_buffer(conf.file_to_open, buffer, report)
                    elif key == curses.KEY_F3: # change to view/tag mode
                        conf.update_viewing_data(win, buffer, report)
                        if file_changes_are_saved(stdscr, conf):
                            conf.disable_file_edit()
                            return conf
                        else:
                            show_file_content(screen, win, buffer, report, conf)
                    elif key == curses.KEY_F4: # add note
                        if report:
                            note_entering = True
                    elif key == curses.KEY_F8: # reload from last save
                        conf.update_viewing_data(win, buffer, report)
                        exit_key = (curses.KEY_F8, "F8")
                        if file_changes_are_saved(stdscr, conf, RELOAD_FILE_WITHOUT_SAVING, exit_key):
                            buffer.lines = buffer.last_save.copy()
                            if report:
                                report.code_review = report.last_save.copy()
                    elif key == curses.KEY_F9: # set filter
                        user_input = UserInput()
                        if conf.content_filter_on():
                            user_input.text = list(conf.filter.content)
                        conf = filter_management(stdscr, screen, win, user_input, conf)
                        """ rewrite screen in case that windows were resized during filter mgmnt - bcs line numbers were set / unset """
                        screen = conf.right_screen if conf.edit_allowed else conf.right_up_screen
                        win = conf.right_win if conf.edit_allowed else conf.right_up_win
                        show_file_content(screen, win, buffer, report, conf, user_input if note_entering else None)
                        if not conf.edit_allowed:
                            show_tags(conf.right_down_screen, conf.right_down_win, conf.tags, conf)

                        conf.update_viewing_data(win, buffer, report)
                        conf.set_brows_mode()
                        conf.quick_view = True
                        conf.left_win.reset_shifts()
                        conf.left_win.set_cursor(0,0)
                        return conf
                    # ======================= CTRL KEYS =======================
                    elif curses.ascii.ismeta(key):
                        """ CTRL + UP / CTRL + DOWN """
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '7' or hex(key) == "0x237": # CTRL + UP: jump to prev note
                            if report and conf.note_highlight:
                                prev_line = report.get_prev_line_with_note(win.cursor.row)
                                while win.cursor.row != prev_line:
                                    win.up(buffer, use_restrictions=True)
                        elif ctrl_key == '^N' or hex(key) == "0x20e": # CTRL + DOWN: jump to next note
                            if report and conf.note_highlight:
                                next_line = report.get_next_line_with_note(win.cursor.row)
                                while win.cursor.row != next_line:
                                    win.down(buffer, filter_on=conf.content_filter_on(), use_restrictions=True)
                    elif curses.ascii.iscntrl(key):
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '^L': # reload from original buffer
                            buffer.lines = buffer.original_buff.copy()
                            if report:
                                report.code_review = report.original_report.copy()
                        elif ctrl_key == '^N': # enable/disable line numbers
                            if conf.line_numbers:
                                conf.disable_line_numbers()
                            else:
                                conf.enable_line_numbers(buffer)
                            resize_all(stdscr, conf, True)
                            win = conf.right_win if conf.edit_allowed else conf.right_up_win
                        elif ctrl_key == '^H': # enable/disable note highlight
                            conf.note_highlight = not conf.note_highlight
                        elif ctrl_key == '^R': # remove all notes on current line
                            if report:
                                report.delete_notes_on_line(win.cursor.row)
                        elif ctrl_key == '^E': # edit note
                            # TODO : note management / note editing  in separate window
                            """
                            if report:
                                line_notes = report.get_notes_on_line(win.cursor.row-1)
                                if len(line_notes) == 1:
                                    # open note for edit
                                    y, x, text = line_notes[0]
                                    report.delete_note(y, x)
                                    user_input.text = list(text)
                                    note_entering = True
                                elif len(line_notes) > 1:
                                    # choose which note you want to edit
                                    log(len(line_notes))
                                    pass
                            """
                            pass
                # ***************************** E.D.I.T *****************************
                # ************************* V.I.E.W / T.A.G *************************
                else:
                    # ======================= F KEYS =======================
                    if key == curses.KEY_F4: # change to edit mode
                        conf.enable_file_edit()
                        return conf
                    elif key == curses.KEY_F9: # set filter
                        user_input = UserInput()
                        if conf.content_filter_on():
                            user_input.text = list(conf.filter.content)
                        conf = filter_management(stdscr, screen, win, user_input, conf)
                        """ rewrite screen in case that windows were resized during filter mgmnt """
                        screen = conf.right_screen if conf.edit_allowed else conf.right_up_screen
                        win = conf.right_win if conf.edit_allowed else conf.right_up_win
                        show_file_content(screen, win, buffer, report, conf, user_input if note_entering else None)
                        if not conf.edit_allowed:
                            show_tags(conf.right_down_screen, conf.right_down_win, conf.tags, conf)

                        conf.update_viewing_data(win, buffer, report)
                        conf.set_brows_mode()
                        conf.quick_view = True
                        conf.left_win.reset_shifts()
                        conf.left_win.set_cursor(0,0)
                        return conf
                    # ======================= CTRL KEYS =======================
                    elif curses.ascii.iscntrl(key):
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '^N': # enable/disable line numbers
                            if conf.line_numbers:
                                conf.disable_line_numbers()
                            else:
                                conf.enable_line_numbers(buffer)
                            resize_all(stdscr, conf, True)
                            win = conf.right_win if conf.edit_allowed else conf.right_up_win
                        elif ctrl_key == '^H': # enable/disable note highlight
                            conf.note_highlight = not conf.note_highlight

                # ************************* V.I.E.W / T.A.G *************************
        except Exception as err:
            log("viewing Exception | "+str(err))
            conf.set_exit_mode()
            return conf


""" **************************** END VIEWING **************************** """


""" **************** BUFFER **************** """

"""
load file content to buffer and file tags to conf
returns: config, buffer, succes
"""
def load_buffer_and_tags(conf):
    """ try load file content to buffer """
    file_already_loaded = False
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
            return conf, None, False

    """ try load file tags to config - only for view, tags will not change """
    if (not conf.tags or not file_already_loaded): # tag file wasnt loaded yet
        tags = load_tags_from_file(conf.file_to_open)
        if not tags:
            conf.set_exit_mode()
            return conf, None, False
        else:
            conf.tags = tags

    return conf, buffer, True


def save_buffer(file_name, buffer, report=None):
    with open(file_name, 'w') as f:
        lines = '\n'.join(buffer.lines)
        f.write(lines)
    buffer.set_save_status(True)
    buffer.last_save = buffer.lines.copy()
    if report:
        save_report_to_file(report)
        report.last_save = report.code_review.copy()



""" **************** REPORT **************** """
def get_report_file_name(path):
    file_name = os.path.splitext(path)[:-1]
    return str(os.path.join(*file_name))+"_report.yaml"


def load_report_from_file(path):
    report_file = get_report_file_name(path)
    report = None
    try:
        with open(report_file, 'r') as f:
            data = yaml.safe_load(f)
        report = Report(report_file, data)
    except yaml.YAMLError as err:
        report = Report(report_file, {})
    except FileNotFoundError:
        report = Report(report_file, {})
    except Exception as err:
        log("load report | "+str(err))

    return report


def save_report_to_file(report):
    with open(report.path, 'w+', encoding='utf8') as f:
        yaml.dump(report.code_review, f, default_flow_style=False, allow_unicode=True)


""" **************** TAGS **************** """
def get_tags_file_name(path):
    file_name = os.path.splitext(path)[:-1]
    return str(os.path.join(*file_name))+"_tags.yaml"


def load_tags_from_file(path):
    tags_file = get_tags_file_name(path)
    tags = None
    try:
        with open(tags_file, 'r') as f:
            data = yaml.safe_load(f)
        tags = Tags(tags_file, data)
    except yaml.YAMLError as err:
        tags = Tags(tags_file, {})
    except FileNotFoundError:
        tags = Tags(tags_file, {})
    except Exception as err:
        log("load tags | "+str(err))

    return tags


def save_tags_to_file(tags):
    with open(tags.path, 'w+', encoding='utf8') as f:
        yaml.dump(tags.data, f, default_flow_style=False, allow_unicode=True)


""" **************************** START TAGGING **************************** """
def tag_management(stdscr, conf):
    curses.curs_set(1)

    screen = conf.right_down_screen
    win = conf.right_down_win

    """ read tags from file """
    if conf.tags: # tag file was already loaded
        tags = conf.tags
    else:
        tags = load_tags_from_file(conf.file_to_open)
        if not tags:
            conf.set_exit_mode()
            return conf
        else:
            conf.tags = tags


    user_input = UserInput()

    while True:
        show_tags(screen, win, tags, conf, user_input)

        """ move cursor to correct position in user input """
        shifted_pointer = user_input.get_shifted_pointer()
        new_row, new_col = win.last_row, win.begin_x+1-win.border+shifted_pointer
        stdscr.move(new_row, new_col)

        key = stdscr.getch()
        try:
            # ======================= EXIT =======================
            if key == curses.KEY_F10:
                tags.save_to_file()
                conf.update_tagging_data(win, tags)
                conf.set_exit_mode()
                user_input.reset()
                return conf
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                tags.save_to_file()
                conf.update_tagging_data(win, tags)
                conf.set_brows_mode()
                user_input.reset()
                return conf
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen, win = conf.right_down_screen, conf.right_down_win
            # ======================= ARROWS =======================
            elif key == curses.KEY_LEFT:
                user_input.left(win)
            elif key == curses.KEY_RIGHT:
                user_input.right(win)
            # ======================= INPUT =======================
            elif key == curses.KEY_DC:
                user_input.delete_symbol(win)
            elif key == curses.KEY_BACKSPACE:
                user_input.left(win)
                if user_input.pointer > 0:
                    user_input.delete_symbol(win)
            elif key == curses.ascii.NL:
                command_parts = ''.join(user_input.text).split()
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
                user_input.reset()
            elif curses.ascii.isprint(key):
                user_input.insert_symbol(win, chr(key))
            # ======================= F KEYS =======================
            elif key == curses.KEY_F4:
                """ F4: edit """
                conf.update_tagging_data(win, tags)
                if not os.path.exists(tags.path):
                    with open(tags.path, 'a+') as f: pass
                conf.set_view_mode()
                conf.enable_file_edit()
                conf.set_file_to_open(tags.path)
                return conf
            elif key == curses.KEY_F9: # set filter
                filter_input = UserInput()
                if conf.tag_filter_on():
                    filter_input.text = list(conf.filter.tag)
                conf = filter_management(stdscr, screen, win, filter_input, conf)
                """ rewrite screen in case that windows were resized during filter mgmnt """
                show_tags(conf.right_down_screen, conf.right_down_win, tags, conf, user_input)
                conf.update_tagging_data(win, tags)
                conf.set_brows_mode()
                conf.quick_view = True
                conf.left_win.reset_shifts()
                conf.left_win.set_cursor(0,0)
                return conf
        except Exception as err:
            log("tagging | "+str(err))
            conf.set_exit_mode()
            return conf

""" **************************** END TAGGING **************************** """


if __name__ == "__main__":
    preparation()

    stdscr = curses.initscr()
    stdscr.keypad(True) # enable read special keys
    curses.wrapper(main)
    curses.endwin()
