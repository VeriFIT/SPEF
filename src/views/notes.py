import curses
import curses.ascii
import yaml
import os
import traceback


from views.help import show_help

from modules.buffer import Tags, UserInput

from views.menu import brows_menu

from utils.loading import save_report_to_file
from utils.input import get_user_input
from utils.screens import *
from utils.printing import *
from utils.logger import *
from utils.coloring import *

from control import *


def notes_management(stdscr, env):
    curses.curs_set(0)
    screen, win = env.get_screen_for_current_mode()

    # report = env.report
    if env.report is None:
        log("unexpected error in note management - there is no report in env")
        env.disable_note_management()
        env.set_view_mode()
        return env


    while True:
        """ print notes """
        rewrite_all_wins(env)

        key = stdscr.getch()
    
        try:
            function = get_function_for_key(env, key)
            if function is not None:
                env, exit_program = run_function(stdscr, env, function, key)
                if exit_program:
                    return env
        except Exception as err:
            log("note management | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env



""" implementation of functions for note management """
def run_function(stdscr, env, fce, key):
    screen, win = env.get_screen_for_current_mode()


    # ==================== EXIT PROGRAM ====================
    if fce == EXIT_PROGRAM:
        env.disable_note_management()
        env.set_exit_mode()
        save_report_to_file(env.report)
        return env, True
    # ================ EXIT NOTE MANAGEMENT ================
    elif fce == EXIT_NOTES:
        env.disable_note_management()
        env.switch_to_next_mode()
        save_report_to_file(env.report)
        return env, True
    # ======================= FOCUS =======================
    elif fce == CHANGE_FOCUS:
        env.switch_to_next_mode()
        return env, True
    # ======================= RESIZE =======================
    elif fce == RESIZE_WIN:
        env = resize_all(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
    # ======================= ARROWS =======================
    elif fce == CURSOR_UP:
        win.up(env.report, use_restrictions=False)
    elif fce == CURSOR_DOWN:
        win.down(env.report, filter_on=env.tag_filter_on(), use_restrictions=False)
    # ===================== SHOW HELP ======================
    elif fce == SHOW_HELP:
        env = show_help(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
    # ===================== EDIT NOTE =====================
    elif fce == EDIT_NOTE:
        if len(env.report.data) > 0 and len(env.report.data) >= win.cursor.row:
            current_note = env.report.data[win.cursor.row]
            user_input = UserInput()
            user_input.text = list(current_note.text)

            # define specific highlight for current line which is related to the new note
            env.specific_line_highlight = (current_note.row, curses.color_pair(NOTE_MGMT))

            title = f"Edit note at {current_note.row}:{current_note.col}"
            env, text = get_user_input(stdscr, env, title=title, user_input=user_input)
            screen, win = env.get_screen_for_current_mode()
            curses.curs_set(0)
            env.specific_line_highlight = None
            if text is not None:
                env.report.data[win.cursor.row].text = ''.join(text)
    # ================== CREATE NEW NOTE ==================
    elif fce == ADD_CUSTOM_NOTE:
        file_win = env.windows.edit if env.edit_allowed else env.windows.view
        note_row, note_col = file_win.cursor.row, file_win.cursor.col - file_win.begin_x

        # define specific highlight for current line which is related to the new note
        env.specific_line_highlight = (note_row, curses.color_pair(NOTE_MGMT))

        title = f"Enter new note at {note_row}:{note_col}"
        env, text = get_user_input(stdscr, env, title=title)
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
        env.specific_line_highlight = None
        if text is not None:
            """ move cursor down if new note is lower then current item (current cursor position) """
            if len(env.report.data) > 0:
                current_note_row = env.report.data[win.cursor.row].row
                current_note_col = env.report.data[win.cursor.row].col
                if note_row < current_note_row or (note_row == current_note_row and note_col < current_note_col):
                    win.down(env.report, filter_on=env.tag_filter_on(), use_restrictions=False)

            """ add note to report """
            env.report.add_note(note_row, note_col, ''.join(text))
    # ================ INSERT TYPICAL NOTE ================
    elif fce == ADD_TYPICAL_NOTE:
        file_win = env.windows.edit if env.edit_allowed else env.windows.view
        note_row, note_col = file_win.cursor.row, file_win.cursor.col - file_win.begin_x

        # define specific highlight for current line which is related to the new note
        env.specific_line_highlight = (note_row, curses.color_pair(NOTE_MGMT))

        title = "Select from typical notes: "
        color = curses.color_pair(GREEN_COL)
        menu_options = [note.text for note in env.typical_notes]
        env, option_idx = brows_menu(stdscr, env, menu_options, color=color, title=title)
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
        env.specific_line_highlight = None
        if option_idx is not None:
            if len(env.typical_notes) >= option_idx:
                """ move cursor down if new note is lower then current item (current cursor position) """
                if len(env.report.data) > 0:
                    current_note_row = env.report.data[win.cursor.row].row
                    current_note_col = env.report.data[win.cursor.row].col
                    if note_row < current_note_row or (note_row == current_note_row and note_col < current_note_col):
                        win.down(env.report, filter_on=env.tag_filter_on(), use_restrictions=False)

                """ add note to report """
                str_text = env.typical_notes[option_idx].text
                env.report.add_note(note_row, note_col, str_text)
    # ==================== GO TO NOTE ====================
    elif fce == GO_TO_NOTE:
        if len(env.report.data) > 0:
            current_note = env.report.data[win.cursor.row]
            env.switch_to_next_mode()
            _, view_win = env.get_screen_for_current_mode()
            if current_note.row < view_win.cursor.row:
                while current_note.row != view_win.cursor.row:
                    view_win.up(env.buffer, use_restrictions=True)
            else:
                while current_note.row != view_win.cursor.row:
                    view_win.down(env.buffer, filter_on=env.content_filter_on(), use_restrictions=True)
            return env, True
    # ================== SAVE AS TYPICAL ==================
    elif fce == SAVE_AS_TYPICAL_NOTE:
        if len(env.report.data) > 0:
            current_note = env.report.data[win.cursor.row]
            if current_note.is_typical(env):
                current_note.remove_from_typical(env)
            else:
                current_note.set_as_typical(env)
    # ==================== DELETE NOTE ====================
    elif fce == DELETE_NOTE:
        if len(env.report.data) > 0 and len(env.report.data) >= win.cursor.row:
            del env.report.data[win.cursor.row]
            if len(env.report.data) <= win.cursor.row:
                win.up(env.report, use_restrictions=False)


    env.update_win_for_current_mode(win)
    return env, False
