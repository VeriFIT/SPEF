
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

from views.filtering import filter_management
from views.help import show_help

from modules.buffer import UserInput

from utils.input import get_user_input
from utils.loading import *
from utils.screens import *
from utils.printing import *
from utils.logger import *

from control import *


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
        return env


    """ try load code review to report  """
    report_already_loaded = False
    report = None
    if buffer.path.startswith(HOME): # opened file is some file from students projects
        project_path = env.get_project_path()
        file_login = os.path.relpath(buffer.path, project_path).split(os.sep)[0]
        report_file = get_report_file_name(buffer.path)
        login_match = bool(re.match(SOLUTION_IDENTIFIER, file_login))
        if login_match:
            if env.report:
                if env.report.path == report_file:
                    report_already_loaded = True
                    report = env.report
            if not env.report or not report_already_loaded:
                # try get report for file in buffer
                report = load_report_from_file(buffer.path)
                env.report = report
    if report is None:
        env.set_exit_mode()
        return env

    """ calculate line numbers """
    if env.line_numbers or env.start_with_line_numbers:
        env.start_with_line_numbers = False
        env.enable_line_numbers(buffer)
        env = resize_all(stdscr, env, True)
        screen, win = env.get_screen_for_current_mode()


    env.buffer = buffer
    env.report = report


    while True:
        """ print all screens """
        # env.update_win_for_current_mode(win)
        screen, win = env.get_screen_for_current_mode()
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
                env, exit_program = run_function(stdscr, env, function, key=key)
                if exit_program:
                    return env

        except Exception as err:
            log("viewing Exception | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env


def get_function_for_key(env, key):
    if key == curses.KEY_F1:
        return env.control.get_function(env, 'F1')
    elif key == curses.KEY_F2:
        return env.control.get_function(env, 'F2')
    elif key == curses.KEY_F3:
        return env.control.get_function(env, 'F3')
    elif key == curses.KEY_F4:
        return env.control.get_function(env, 'F4')
    elif key == curses.KEY_F5:
        return env.control.get_function(env, 'F5')
    elif key == curses.KEY_F6:
        return env.control.get_function(env, 'F6')
    elif key == curses.KEY_F7:
        return env.control.get_function(env, 'F7')
    elif key == curses.KEY_F8:
        return env.control.get_function(env, 'F8')
    elif key == curses.KEY_F9:
        return env.control.get_function(env, 'F9')
    elif key == curses.KEY_F10:
        return env.control.get_function(env, 'F10')
    elif key == curses.KEY_F11:
        return env.control.get_function(env, 'F11')
    elif key == curses.KEY_F12:
        return env.control.get_function(env, 'F12')
    elif key == 27:
        return env.control.get_function(env, 'ESC')
    elif key == curses.ascii.TAB:
        return env.control.get_function(env, 'TAB')
    elif key == curses.KEY_RESIZE:
        return RESIZE_WIN
        # return env.control.get_function(env, 'RESIZE')
    elif key == curses.KEY_UP:
        return env.control.get_function(env, 'UP')
    elif key == curses.KEY_DOWN:
        return env.control.get_function(env, 'DOWN')
    elif key == curses.KEY_LEFT:
        return env.control.get_function(env, 'LEFT')
    elif key == curses.KEY_RIGHT:
        return env.control.get_function(env, 'RIGHT')
    elif key == curses.KEY_DC:
        return env.control.get_function(env, 'DELETE')
    elif key == curses.KEY_BACKSPACE:
        return env.control.get_function(env, 'BACKSPACE')
    elif key == curses.ascii.NL:
        return env.control.get_function(env, 'ENTER')
    elif curses.ascii.isprint(key):
        char_key = chr(key)
        function = None
        # try to find some function for specitic ascii symbols
        if char_key == '\\':
            function = env.control.get_function(env, 'BACKSLASH')
        elif char_key in [str(i) for i in range(0,10)]:
            function = env.control.get_function(env, char_key) # number 0..10
        # ============>>> HERE YOU CAN ADD SPECIFIC SYMBOLS TO MATCH <<<============

        if function is None:
            # if there is no specific function, return general ASCII function
            return env.control.get_function(env, 'ASCII')
        else:
            return function
    if curses.ascii.ismeta(key):
        ctrl_key = curses.ascii.unctrl(key)
        if ctrl_key == '7' or hex(key) == "0x237":
            return env.control.get_function(env, 'CTRL+UP')
        elif ctrl_key == '^N' or hex(key) == "0x20e":
            return env.control.get_function(env, 'CTRL+DOWN')
    elif curses.ascii.iscntrl(key):
        ctrl_key = curses.ascii.unctrl(key)
        if ctrl_key == '^L':
            return env.control.get_function(env, 'CTRL+L')
        elif ctrl_key == '^N':
            return env.control.get_function(env, 'CTRL+N')
        elif ctrl_key == '^R':
            return env.control.get_function(env, 'CTRL+R')
        # ===============>>> HERE YOU CAN ADD CTRL KEYS TO MATCH <<<===============

    return None





""" implementation of functions for file edit/management """
def run_function(stdscr, env, fce, key=None, screen=None, win=None): 
    if screen is None or win is None:
        screen, win = env.get_screen_for_current_mode()

    if fce == EXIT_PROGRAM:
        if file_changes_are_saved(stdscr, env):
            env.set_exit_mode()
            return env, True
    elif fce == SHOW_HELP:
        env = show_help(stdscr, env)
        curses.curs_set(1)
        # screen, win = env.get_screen_for_current_mode()
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
    # ======================= EDIT/MANAGE =======================
    elif fce == SET_EDIT_FILE_MODE:
        env.change_to_file_edit_mode()
    elif fce == SET_MANAGE_FILE_MODE:
        env.change_to_file_management()
    # ======================= LINE NUMBERS =======================
    elif fce == SHOW_OR_HIDE_LINE_NUMBERS:
        if env.line_numbers:
            env.disable_line_numbers()
        else:
            env.enable_line_numbers(env.buffer)
        env = resize_all(stdscr, env, True)
        screen, win = env.get_screen_for_current_mode()
    elif fce == SHOW_OR_HIDE_NOTE_HIGHLIGHT:
        env.note_highlight = not env.note_highlight
    # ======================= SHOW NOTES =======================
    elif fce == OPEN_NOTE_MANAGEMENT:
        env.enable_note_management()
        env.switch_to_next_mode()
        return env, True
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
    # ======================= FOCUS =======================
    elif fce == CHANGE_FOCUS:
        if env.edit_allowed:
            if file_changes_are_saved(stdscr, env):
                env.switch_to_next_mode()
                return env, True
        else:
            env.switch_to_next_mode()
            return env, True
    # ======================= RESIZE =======================
    elif fce == RESIZE_WIN:
        env = resize_all(stdscr, env)
        # screen, win = env.get_screen_for_current_mode()
    # ======================= ARROWS =======================
    elif fce == CURSOR_UP:
        win.up(env.buffer, use_restrictions=True)
        win.calculate_tab_shift(env.buffer, env.tab_size)
        # env.update_win_for_current_mode(win)
    elif fce == CURSOR_DOWN:
        win.down(env.buffer, filter_on=env.content_filter_on(), use_restrictions=True)
        win.calculate_tab_shift(env.buffer, env.tab_size)
        # env.update_win_for_current_mode(win)
    elif fce == CURSOR_LEFT:
        win.left(env.buffer)
        win.calculate_tab_shift(env.buffer, env.tab_size)
        # env.update_win_for_current_mode(win)
    elif fce == CURSOR_RIGHT:
        win.right(env.buffer, filter_on=env.content_filter_on())
        win.calculate_tab_shift(env.buffer, env.tab_size)
        # env.update_win_for_current_mode(win)

    # ======================= NOTES JUMP =======================
    elif fce == GO_TO_PREV_NOTE:
        if env.report and env.note_highlight:
            prev_line = env.report.get_prev_line_with_note(win.cursor.row)
            while win.cursor.row != prev_line:
                win.up(env.buffer, use_restrictions=True)
            win.calculate_tab_shift(env.buffer, env.tab_size)
            env.update_win_for_current_mode(win)

    elif fce == GO_TO_NEXT_NOTE:
        if env.report and env.note_highlight:
            next_line = env.report.get_next_line_with_note(win.cursor.row)
            while win.cursor.row != next_line:
                win.down(env.buffer, filter_on=env.content_filter_on(), use_restrictions=True)
            win.calculate_tab_shift(env.buffer, env.tab_size)
            env.update_win_for_current_mode(win)

    # ======================= RELOAD =======================
    elif fce == RELOAD_ORIGINAL_BUFF:
        env.buffer.lines = env.buffer.original_buff.copy()
        env.report.data = env.report.original_report.copy()
    elif fce == RELOAD_FILE_FROM_LAST_SAVE:
        exit_key = (key, key) # !!!!!!! TODO !!!!!!!
        if file_changes_are_saved(stdscr, env, RELOAD_FILE_WITHOUT_SAVING, exit_key):
            env.buffer.lines = env.buffer.last_save.copy()
            env.report.data = env.report.last_save.copy()
    else:
        if env.file_edit_mode:
            # ======================= EDIT FILE =======================
            if fce == DELETE:
                env.report = env.buffer.delete(win, env.report)
                # env.update_win_for_current_mode(win)

            elif fce == BACKSPACE:
                if (win.cursor.row, win.cursor.col) > (win.begin_y, win.begin_x):
                    win.left(env.buffer)
                    env.report = env.buffer.delete(win, env.report)
                    win.calculate_tab_shift(env.buffer, env.tab_size)
                    # env.update_win_for_current_mode(win)

            elif fce == PRINT_NEW_LINE:
                env.report = env.buffer.newline(win, env.report)
                win.right(env.buffer, filter_on=env.content_filter_on())
                win.calculate_tab_shift(env.buffer, env.tab_size)
                # env.update_win_for_current_mode(win)

            elif fce == PRINT_CHAR:
                if key is not None:
                    env.buffer.insert(win, chr(key))
                    win.right(env.buffer, filter_on=env.content_filter_on())
                    win.calculate_tab_shift(env.buffer, env.tab_size)
                    # env.update_win_for_current_mode(win)
        else:
            # ======================= MANAGE FILE =======================
            if fce == FILTER:
                env = filter_management(stdscr, screen, win, env)
                # screen, win = env.get_screen_for_current_mode()
                # env.update_win_for_current_mode(win)
                env.prepare_browsing_after_filter()
                return env, True
            elif fce == ADD_CUSTOM_NOTE:
                note_row, note_col = win.cursor.row, win.cursor.col - win.begin_x
                # define specific highlight for current line which is related to the new note
                env.specific_line_highlight = (note_row, curses.color_pair(NOTE_MGMT))

                title = f"Enter new note at {note_row}:{note_col}"
                env, text = get_user_input(stdscr, env, title=title)
                # screen, win = env.get_screen_for_current_mode()
                curses.curs_set(1)
                env.specific_line_highlight = None
                if text is not None:
                    env.report.add_note(note_row, note_col, ''.join(text))
            elif fce == ADD_TYPICAL_NOTE:
                char_key = chr(key)
                int_key = int(char_key)
                if len(env.typical_notes) >= int_key:
                    str_text = env.typical_notes[int_key-1].text                              
                    note_row, note_col = win.cursor.row, win.cursor.col - win.begin_x
                    env.report.add_note(note_row, note_col, str_text)

    env.update_win_for_current_mode(win)

    return env, False

