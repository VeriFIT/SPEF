
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

    """ calculate line numbers """
    if env.line_numbers:
        env.enable_line_numbers(buffer)
        env = resize_all(stdscr, env, True)
        screen, win = env.get_screen_for_current_mode()


    while True:
        """ print all screens """
        env.update_viewing_data(win, buffer, report)
        rewrite_all_wins(env)

        try:
            """ move cursor to correct position """
            new_row, new_col = win.get_cursor_position()
            stdscr.move(new_row, new_col)
        except Exception as err:
            log("move cursor | "+str(err))
            env.set_exit_mode()
            return env

        key = stdscr.getch()

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
                        env.switch_to_next_mode()
                        return env
                else:
                    env.switch_to_next_mode()
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
            # ================ F KEYS - EDIT AND VIEW ================
            elif key == curses.KEY_F1: # show help
                env = show_help(stdscr, env)
                screen, win = env.get_screen_for_current_mode()
                curses.curs_set(1)
            elif key == curses.KEY_F5: # enable/disable line numbers
                if env.line_numbers:
                    env.disable_line_numbers()
                else:
                    env.enable_line_numbers(buffer)
                env = resize_all(stdscr, env, True)
                screen, win = env.get_screen_for_current_mode()
            elif key == curses.KEY_F6: # enable/disable note highlight
                env.note_highlight = not env.note_highlight
            elif key == curses.KEY_F9: # set filter
                env = filter_management(stdscr, screen, win, env)
                screen, win = env.get_screen_for_current_mode()
                env.update_viewing_data(win, buffer, report)
                env.prepare_browsing_after_filter()
                return env
            else:
                if env.edit_allowed:
                    # ------------------------ EDIT FILE ------------------------
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
                    # ------------------------ F KEYS - EDIT ------------------------
                    elif key == curses.KEY_F2: # save file
                        save_buffer(env.file_to_open, buffer, report)
                    elif key == curses.KEY_F3: # change to view/tag mode
                        env.update_viewing_data(win, buffer, report)
                        if file_changes_are_saved(stdscr, env):
                            env.disable_file_edit()
                            return env
                    elif key == curses.KEY_F4: # add note
                        pass
                        # if report:
                            # note_entering = True
                        env.update_viewing_data(win, buffer, report)
                        env.enable_note_management()
                        env.switch_to_next_mode()
                        return env
                    elif key == curses.KEY_F8: # reload from last save
                        env.update_viewing_data(win, buffer, report)
                        exit_key = (curses.KEY_F8, "F8")
                        if file_changes_are_saved(stdscr, env, RELOAD_FILE_WITHOUT_SAVING, exit_key):
                            buffer.lines = buffer.last_save.copy()
                            if report:
                                report.code_review = report.last_save.copy()
                    # ------------------------ CTRL KEYS - EDIT ------------------------
                    elif curses.ascii.ismeta(key): # jump between notes in file
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '7' or hex(key) == "0x237": # CTRL + UP: jump to prev note
                            if report and env.note_highlight:
                                prev_line = report.get_prev_line_with_note(win.cursor.row)
                                while win.cursor.row != prev_line:
                                    win.up(buffer, use_restrictions=True)
                                win.calculate_tab_shift(buffer, env.tab_size)
                        elif ctrl_key == '^N' or hex(key) == "0x20e": # CTRL + DOWN: jump to next note
                            if report and env.note_highlight:
                                next_line = report.get_next_line_with_note(win.cursor.row)
                                while win.cursor.row != next_line:
                                    win.down(buffer, filter_on=env.content_filter_on(), use_restrictions=True)
                                win.calculate_tab_shift(buffer, env.tab_size)
                    elif curses.ascii.iscntrl(key):
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '^L': # reload from original buffer
                            buffer.lines = buffer.original_buff.copy()
                            if report:
                                report.code_review = report.original_report.copy()
                        elif ctrl_key == '^N':
                            pass
                        elif ctrl_key == '^H':
                            pass
                        elif ctrl_key == '^R':
                            pass
                        elif ctrl_key == '^E':
                            pass

                else:
                    # ------------------------ F KEYS - VIEW ------------------------
                    if key == curses.KEY_F2:
                        pass
                    elif key == curses.KEY_F4: # change to edit mode
                        env.enable_file_edit()
                        return env
                    # ------------------------ CTRL KEYS - VIEW ------------------------
                    elif curses.ascii.iscntrl(key):
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '^N':
                            pass
                        elif ctrl_key == '^H':
                            pass
        except Exception as err:
            log("viewing Exception | "+str(err))
            env.set_exit_mode()
            return env

