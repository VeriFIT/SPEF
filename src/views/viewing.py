
import curses
import curses.ascii
import json
import yaml
import os
import re
import sys
import fnmatch
import glob
import traceback
import time

from controls.control import *

from views.filtering import filter_management
from views.help import show_help
from views.input import get_user_input

from modules.buffer import UserInput

from utils.loading import *
from utils.screens import *
from utils.printing import *
from utils.logger import *


# TODO: project config
SOLUTION_IDENTIFIER = "x[a-z]{5}[0-9]{2}"



def file_viewing(stdscr, env):
    curses.curs_set(1) # set cursor as visible
    screen, win = env.get_screen_for_current_mode()

    if not env.file_to_open: # there is no file to open
        env.set_brows_mode()
        return env

    """ try load file content and tags """
    env, buffer, succ = load_buffer_and_tags(env)
    if not succ:
        env.set_file_to_open(None)
        env.set_brows_mode() # instead of exit mode
        return env


    # check if file is from some project directory
    # buffer_dir = Directory(os.path.dirname(buffer.path))
    # if buffer_dir.is_project_subdirectory():
        # proj = load_proj_from_conf_file(buffer_dir.proj_conf_path)

    # check if file is from student solution directory (match solution id)
    # file_login = os.path.relpath(buffer.path, project_path).split(os.sep)[0]
    # report_file = get_report_file_name(buffer.path)
    # login_match = bool(re.match(SOLUTION_IDENTIFIER, file_login))
    # if login_match:

    """ try load code review to report  """
    report_already_loaded = False
    report = None
    if env.report:
        if env.report.path == report_file:
            report_already_loaded = True
            report = env.report
    if not env.report or not report_already_loaded:
        # try get report for file in buffer
        report = load_report_from_file(buffer.path)
        env.report = report


    """ calculate line numbers """
    if env.line_numbers or env.start_with_line_numbers:
        env.start_with_line_numbers = False
        env.enable_line_numbers(buffer)
        env = resize_all(stdscr, env, True)
        screen, win = env.get_screen_for_current_mode()


    env.buffer = buffer
    env.report = report
    rewrite = True

    while True:
        """ print all screens """
        screen, win = env.get_screen_for_current_mode()
        if rewrite:
            rewrite_all_wins(env)

        try:
            """ move cursor to correct position """
            new_row, new_col = win.get_cursor_position()
            stdscr.move(new_row, new_col)
        except Exception as err:
            log("move cursor | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env

        key = stdscr.getch()

        try:
            function = get_function_for_key(env, key)
            if function is not None:
                env, rewrite, exit_view = run_function(stdscr, env, function, key)
                if exit_view:
                    return env
        except Exception as err:
            log("viewing Exception | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env


""" implementation of functions for file edit/management """
def run_function(stdscr, env, fce, key):
    screen, win = env.get_screen_for_current_mode()
    rewrite = False

    # ======================= EXIT =======================
    if fce == EXIT_PROGRAM:
        if file_changes_are_saved(stdscr, env):
            env.set_exit_mode()
            return env, rewrite, True
        rewrite = True
    # ======================= FOCUS =======================
    elif fce == CHANGE_FOCUS:
        if env.edit_allowed:
            if file_changes_are_saved(stdscr, env):
                env.switch_to_next_mode()
                return env, rewrite, True
            rewrite = True
        else:
            env.switch_to_next_mode()
            return env, rewrite, True
    # ======================= RESIZE =======================
    elif fce == RESIZE_WIN:
        env = resize_all(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
        rewrite = True
    # ======================= ARROWS =======================
    elif fce == CURSOR_UP:
        old_shifts = win.row_shift, win.col_shift
        win.up(env.buffer, use_restrictions=True)
        win.calculate_tab_shift(env.buffer, env.tab_size)
        rewrite = (old_shifts != (win.row_shift, win.col_shift))
    elif fce == CURSOR_DOWN:
        old_shifts = win.row_shift, win.col_shift
        win.down(env.buffer, filter_on=env.content_filter_on(), use_restrictions=True)
        win.calculate_tab_shift(env.buffer, env.tab_size)
        rewrite = (old_shifts != (win.row_shift, win.col_shift))
    elif fce == CURSOR_LEFT:
        old_shifts = win.row_shift, win.col_shift
        win.left(env.buffer)
        win.calculate_tab_shift(env.buffer, env.tab_size)
        rewrite = (old_shifts != (win.row_shift, win.col_shift))
    elif fce == CURSOR_RIGHT:
        old_shifts = win.row_shift, win.col_shift
        win.right(env.buffer, filter_on=env.content_filter_on())
        win.calculate_tab_shift(env.buffer, env.tab_size)
        rewrite = (old_shifts != (win.row_shift, win.col_shift))
    # ======================= SHOW HELP =======================
    elif fce == SHOW_HELP:
        env = show_help(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(1)
        rewrite = True
    # ======================= SAVE FILE =======================
    elif fce == SAVE_FILE:
        save_buffer(env.file_to_open, env.buffer, env.report)
    # ======================= SHOW/HIDE TAGS =======================
    elif fce == SHOW_OR_HIDE_TAGS:
        # env.show_tags = not env.show_tags
        if env.edit_allowed:
            env.disable_file_edit()
        else:
            env.enable_file_edit()
        screen, win = env.get_screen_for_current_mode()
        rewrite = True
    # ======================= LINE NUMBERS =======================
    elif fce == SHOW_OR_HIDE_LINE_NUMBERS:
        if env.line_numbers:
            env.disable_line_numbers()
        else:
            env.enable_line_numbers(env.buffer)
        env = resize_all(stdscr, env, True)
        screen, win = env.get_screen_for_current_mode()
        rewrite = True
    elif fce == SHOW_OR_HIDE_NOTE_HIGHLIGHT:
        env.note_highlight = not env.note_highlight
        rewrite = True
    # ======================= SHOW NOTES =======================
    elif fce == OPEN_NOTE_MANAGEMENT:
        env.enable_note_management()
        env.switch_to_next_mode()
        return env, rewrite, True
    elif fce == SHOW_TYPICAL_NOTES:
        center_screen, center_win = env.get_center_win(reset=True)
        max_cols = center_win.end_x - center_win.begin_x
        max_rows = center_win.end_y - center_win.begin_y
        options = {}
        if len(env.typical_notes) > 0:
            if len(env.typical_notes) < 9:
                for idx, note in enumerate(env.typical_notes):
                    options[str(idx+1)] = note.text
        custom_help = (None, "Typical notes:", options)
        curses.curs_set(0)
        print_help(center_screen, max_cols, max_rows, env, custom_help=custom_help)
        key = stdscr.getch()
        curses.curs_set(1)
        rewrite = True
    # ======================= NOTES JUMP =======================
    elif fce == GO_TO_PREV_NOTE:
        if env.report and env.note_highlight:
            old_shifts = win.row_shift, win.col_shift # get old shifts
            prev_line = env.report.get_prev_line_with_note(win.cursor.row)
            while win.cursor.row != prev_line:
                win.up(env.buffer, use_restrictions=True)
            win.calculate_tab_shift(env.buffer, env.tab_size)
            env.update_win_for_current_mode(win)
            rewrite = (old_shifts != (win.row_shift, win.col_shift)) # rewrite if shifts changed
    elif fce == GO_TO_NEXT_NOTE:
        if env.report and env.note_highlight:
            old_shifts = win.row_shift, win.col_shift # get old shifts
            next_line = env.report.get_next_line_with_note(win.cursor.row)
            while win.cursor.row != next_line:
                win.down(env.buffer, filter_on=env.content_filter_on(), use_restrictions=True)
            win.calculate_tab_shift(env.buffer, env.tab_size)
            env.update_win_for_current_mode(win)
            rewrite = (old_shifts != (win.row_shift, win.col_shift)) # rewrite if shifts changed
    # ======================= RELOAD =======================
    elif fce == RELOAD_ORIGINAL_BUFF:
        env.buffer.lines = env.buffer.original_buff.copy()
        if env.report:
            env.report.data = env.report.original_report.copy()
        rewrite = True
    elif fce == RELOAD_FILE_FROM_LAST_SAVE:
        if file_changes_are_saved(stdscr, env, RELOAD_FILE_WITHOUT_SAVING):
            env.buffer.lines = env.buffer.last_save.copy()
            if env.report:
                env.report.data = env.report.last_save.copy()
        rewrite = True
    else:
        if env.file_edit_mode:
            # ======================= EDIT FILE =======================
            if fce == DELETE:
                old_len = len(env.buffer)
                env.report = env.buffer.delete(win, env.report)
                if old_len == len(env.buffer):
                    env.update_win_for_current_mode(win)
                    rewrite_one_line_in_file(env, win.cursor.row)
                else:
                    rewrite = True
            elif fce == BACKSPACE:
                old_len = len(env.buffer)
                if (win.cursor.row, win.cursor.col) > (win.begin_y, win.begin_x):
                    win.left(env.buffer)
                    env.report = env.buffer.delete(win, env.report)
                    win.calculate_tab_shift(env.buffer, env.tab_size)
                if old_len == len(env.buffer):
                    env.update_win_for_current_mode(win)
                    rewrite_one_line_in_file(env, win.cursor.row)
                else:
                    rewrite = True
            elif fce == PRINT_NEW_LINE:
                env.report = env.buffer.newline(win, env.report)
                win.right(env.buffer, filter_on=env.content_filter_on())
                win.calculate_tab_shift(env.buffer, env.tab_size)
                rewrite = True
            elif fce == PRINT_CHAR:
                old_len = len(env.buffer)
                if key is not None:
                    env.buffer.insert(win, chr(key))
                    win.right(env.buffer, filter_on=env.content_filter_on())
                    win.calculate_tab_shift(env.buffer, env.tab_size)
                if old_len == len(env.buffer):
                    env.update_win_for_current_mode(win)
                    rewrite_one_line_in_file(env, win.cursor.row)
                else:
                    rewrite = True
            # ======================= EDIT -> MANAGE =======================
            elif fce == SET_MANAGE_FILE_MODE:
                env.change_to_file_management()
        else:
            # ======================= FILTER =======================
            if fce == FILTER:
                env = filter_management(stdscr, screen, win, env)
                if env.is_exit_mode() or env.is_brows_mode():
                    return env, rewrite, True
                rewrite = True
            # ======================= MANAGE -> EDIT =======================
            elif fce == SET_EDIT_FILE_MODE:
                log("edit "+str(SET_EDIT_FILE_MODE))
                env.change_to_file_edit_mode()
            # ======================= ADD NOTES =======================
            elif fce == ADD_CUSTOM_NOTE:
                if env.report:
                    note_row, note_col = win.cursor.row, win.cursor.col - win.begin_x
                    # define specific highlight for current line which is related to the new note
                    env.specific_line_highlight = (note_row, curses.color_pair(COL_NOTE_LIGHT))

                    title = f"Enter new note at {note_row}:{note_col}"
                    env, text = get_user_input(stdscr, env, title=title)
                    screen, win = env.get_screen_for_current_mode()
                    curses.curs_set(1)
                    env.specific_line_highlight = None
                    if text is not None:
                        env.report.add_note(note_row, note_col, ''.join(text))
                    rewrite = True
            elif fce == ADD_TYPICAL_NOTE:
                if env.report:
                    char_key = chr(key)
                    int_key = int(char_key)
                    if len(env.typical_notes) >= int_key:
                        str_text = env.typical_notes[int_key-1].text
                        note_row, note_col = win.cursor.row, win.cursor.col - win.begin_x
                        env.report.add_note(note_row, note_col, str_text)
                    rewrite = True
    env.update_win_for_current_mode(win)
    return env, rewrite, False

