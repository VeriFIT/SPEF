
import curses
import curses.ascii
import json
import yaml
import os
import re
import sys
import fnmatch
import glob


from views.filtering import filter_management
from views.help import show_help

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


    if not env.file_to_open: # there is no file to open and edit
        env.set_brows_mode()
        return env


    """ try load file content and tags """
    env, buffer, succ = load_buffer_and_tags(env)
    if not succ:
        return env


    """ try load code review to report  """
    report_already_loaded = False
    env.note_highlight = False
    report = None
    if buffer.path.startswith(HOME): # opened file is some file from students projects
        project_path = env.get_project_path()
        file_login = os.path.relpath(buffer.path, project_path).split(os.sep)[0]
        report_file = get_report_file_name(buffer.path)
        login_match = bool(re.match(SOLUTION_IDENTIFIER, file_login))
        if login_match:
            env.note_highlight = True
            if env.report:
                if env.report.path == report_file:
                    report_already_loaded = True
                    report = env.report
            if not env.report or not report_already_loaded:
                # try get report for file in buffer
                try:
                    report = load_report_from_file(buffer.path)
                    env.report = report
                except Exception as err:
                    log("load file report | "+str(err))
                    env.set_exit_mode()
                    return env

    note_entering = False
    user_input = UserInput()

    """ calculate line numbers """
    if env.line_numbers:
        env.enable_line_numbers(buffer)
        env = resize_all(stdscr, env, True)
        win = env.windows.right if env.edit_allowed else env.windows.right_up
        win.set_line_num_shift(len(env.line_numbers)+1)


    while True:
        """ print all screens """
        env.update_viewing_data(win, buffer, report)
        rewrite_all_wins(env)

        try:
            """ move cursor to correct position """
            if note_entering:
                shifted_pointer = user_input.get_shifted_pointer()
                new_row, new_col = win.last_row, win.begin_x+1-win.border+shifted_pointer
                if env.line_numbers:
                    new_col -= win.line_num_shift
                stdscr.move(new_row, new_col)
            else:
                new_row, new_col = win.get_cursor_position()
                stdscr.move(new_row, new_col)
        except Exception as err:
            log("move cursor | "+str(err))
            env.set_exit_mode()
            return env

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
                save_report_to_file(report)
                note_entering = False
                user_input.reset()
            elif curses.ascii.isprint(key):
                user_input.insert_symbol(win, chr(key))
            continue

        try:
            # ======================= EXIT =======================
            if key == curses.KEY_F10:
                env.update_viewing_data(win, buffer, report)
                if file_changes_are_saved(stdscr, env):
                    env.set_exit_mode()
                    return env
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                env.update_viewing_data(win, buffer, report)
                if env.edit_allowed:
                    if file_changes_are_saved(stdscr, env):
                        env.set_brows_mode()
                        return env
                else:
                    env.set_tag_mode()
                    return env
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(buffer, use_restrictions=True)
                win.calculate_tab_shift(buffer, env.tab_size)
            elif key == curses.KEY_DOWN:
                win.down(buffer, filter_on=env.content_filter_on(), use_restrictions=True)
                win.calculate_tab_shift(buffer, env.tab_size)
            elif key == curses.KEY_LEFT:
                win.left(buffer)
                win.calculate_tab_shift(buffer, env.tab_size)
            elif key == curses.KEY_RIGHT:
                win.right(buffer, filter_on=env.content_filter_on())
                win.calculate_tab_shift(buffer, env.tab_size)
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                env = resize_all(stdscr, env)
                screen, win = env.get_screen_for_current_mode()
            else:
                # ***************************** E.D.I.T *****************************
                if env.edit_allowed:
                    # ======================= EDIT FILE =======================
                    if key == curses.KEY_DC: # \x04 for MacOS which doesnt correctly decode delete key
                        report = buffer.delete(win, report)
                    elif key == curses.KEY_BACKSPACE: # \x7f for MacOS
                        if (win.cursor.row, win.cursor.col) > (win.begin_y, win.begin_x):
                            win.left(buffer)
                            report = buffer.delete(win, report)
                            win.calculate_tab_shift(buffer, env.tab_size)
                    elif key == curses.ascii.NL:
                        report = buffer.newline(win, report)
                        win.right(buffer, filter_on=env.content_filter_on())
                        win.calculate_tab_shift(buffer, env.tab_size)
                    elif curses.ascii.isprint(key):
                        buffer.insert(win, chr(key))
                        win.right(buffer, filter_on=env.content_filter_on())
                        win.calculate_tab_shift(buffer, env.tab_size)
                    # ======================= F KEYS =======================
                    elif key == curses.KEY_F1: # help
                        env = show_help(stdscr, env)
                        screen, win = env.get_screen_for_current_mode()
                        curses.curs_set(1)
                    elif key == curses.KEY_F2: # save file
                        save_buffer(env.file_to_open, buffer, report)
                    elif key == curses.KEY_F3: # change to view/tag mode
                        env.update_viewing_data(win, buffer, report)
                        if file_changes_are_saved(stdscr, env):
                            env.disable_file_edit()
                            return env
                    elif key == curses.KEY_F4: # add note
                        if report:
                            note_entering = True
                    elif key == curses.KEY_F8: # reload from last save
                        env.update_viewing_data(win, buffer, report)
                        exit_key = (curses.KEY_F8, "F8")
                        if file_changes_are_saved(stdscr, env, RELOAD_FILE_WITHOUT_SAVING, exit_key):
                            buffer.lines = buffer.last_save.copy()
                            if report:
                                report.code_review = report.last_save.copy()
                    elif key == curses.KEY_F9: # set filter
                        env = filter_management(stdscr, screen, win, env)
                        env.update_viewing_data(win, buffer, report)
                        env.set_brows_mode()
                        env.quick_view = True
                        env.windows.left.reset_shifts()
                        env.windows.left.set_cursor(0,0)
                        return env
                    # ======================= CTRL KEYS =======================
                    elif curses.ascii.ismeta(key):
                        """ CTRL + UP / CTRL + DOWN """
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '7' or hex(key) == "0x237": # CTRL + UP: jump to prev note
                            if report and env.note_highlight:
                                prev_line = report.get_prev_line_with_note(win.cursor.row)
                                while win.cursor.row != prev_line:
                                    win.up(buffer, use_restrictions=True)
                        elif ctrl_key == '^N' or hex(key) == "0x20e": # CTRL + DOWN: jump to next note
                            if report and env.note_highlight:
                                next_line = report.get_next_line_with_note(win.cursor.row)
                                while win.cursor.row != next_line:
                                    win.down(buffer, filter_on=env.content_filter_on(), use_restrictions=True)
                    elif curses.ascii.iscntrl(key):
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '^L': # reload from original buffer
                            buffer.lines = buffer.original_buff.copy()
                            if report:
                                report.code_review = report.original_report.copy()
                        elif ctrl_key == '^N': # enable/disable line numbers
                            if env.line_numbers:
                                env.disable_line_numbers()
                            else:
                                env.enable_line_numbers(buffer)
                            resize_all(stdscr, env, True)
                            win = env.windows.right if env.edit_allowed else env.windows.right_up
                        elif ctrl_key == '^H': # enable/disable note highlight
                            env.note_highlight = not env.note_highlight
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
                    if key == curses.KEY_F1: # help
                        show_help(stdscr, env)
                        curses.curs_set(1)
                    elif key == curses.KEY_F4: # change to edit mode
                        env.enable_file_edit()
                        return env
                    elif key == curses.KEY_F9: # set filter
                        env = filter_management(stdscr, screen, win, env)
                        screen, win = env.get_screen_for_current_mode()
                        env.update_viewing_data(win, buffer, report)
                        env.set_brows_mode()
                        env.quick_view = True
                        env.windows.left.reset_shifts()
                        env.windows.left.set_cursor(0,0)
                        return env
                    # ======================= CTRL KEYS =======================
                    elif curses.ascii.iscntrl(key):
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '^N': # enable/disable line numbers
                            if env.line_numbers:
                                env.disable_line_numbers()
                            else:
                                env.enable_line_numbers(buffer)
                            resize_all(stdscr, env, True)
                            win = env.windows.right if env.edit_allowed else env.windows.right_up
                        elif ctrl_key == '^H': # enable/disable note highlight
                            env.note_highlight = not env.note_highlight

                # ************************* V.I.E.W / T.A.G *************************
        except Exception as err:
            log("viewing Exception | "+str(err))
            env.set_exit_mode()
            return env

