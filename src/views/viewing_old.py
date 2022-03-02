
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

# from control import *


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
        # env.update_viewing_data(win, buffer, report)
        env.update_win_for_current_mode(win)
        screen, win = env.get_screen_for_current_mode()

        rewrite_all_wins(env)
        # rewrite_file(env)

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
            # ======================= EXIT =======================
            if key == curses.KEY_F10:
                if file_changes_are_saved(stdscr, env):
                    env.set_exit_mode()
                    return env
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                if env.edit_allowed:
                    if file_changes_are_saved(stdscr, env):
                        env.switch_to_next_mode()
                        return env
                else:
                    env.switch_to_next_mode()
                    return env
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                env = resize_all(stdscr, env)
                # screen, win = env.get_screen_for_current_mode()
                # rewrite_all = True
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                # old_shifts = win.row_shift, win.col_shift
                win.up(env.buffer, use_restrictions=True)
                win.calculate_tab_shift(env.buffer, env.tab_size)
                # if old_shift != (win.row_shift, win.col_shift):
                #     rewrite = True
            elif key == curses.KEY_DOWN:
                # shift_change = win.down(buffer, filter_on=env.content_filter_on(), use_restrictions=True)
                # if shift_change:
                #     rewrite = True
                win.down(env.buffer, filter_on=env.content_filter_on(), use_restrictions=True)
                win.calculate_tab_shift(env.buffer, env.tab_size)
            elif key == curses.KEY_LEFT:
                # shift_change = win.left(buffer)
                # if shift_change:
                #     rewrite = True # TODO: rewrite only lines with change
                win.left(env.buffer)
                win.calculate_tab_shift(env.buffer, env.tab_size)
            elif key == curses.KEY_RIGHT:
                # shift_change = win.right(buffer, filter_on=env.content_filter_on())
                # if shift_change:
                #     rewrite = True # TODO: rewrite only lines with change
                win.right(env.buffer, filter_on=env.content_filter_on())
                win.calculate_tab_shift(env.buffer, env.tab_size)
            # ======================= F KEYS =======================
            elif key == curses.KEY_F1: # show help
                env = show_help(stdscr, env)
                curses.curs_set(1)
                # screen, win = env.get_screen_for_current_mode()
                # rewrite_all = True
            elif key == curses.KEY_F2: # save file
                save_buffer(env.file_to_open, env.buffer, env.report)
            elif key == curses.KEY_F3: # change to view/tag mode --> TODO: show/hide tags
                # env.update_viewing_data(win, buffer, report)
                # env.show_tags = not env.show_tags

                # if file_changes_are_saved(stdscr, env):
                if env.edit_allowed:
                    env.disable_file_edit()
                else:
                    env.enable_file_edit()
                screen, win = env.get_screen_for_current_mode()
                # rewrite = True
                # return env
            elif key == curses.KEY_F4: # add note --> TODO: edit file
                env.change_to_file_edit_mode()
            elif key == curses.KEY_F5: # show/hide line numbers
                if env.line_numbers:
                    env.disable_line_numbers()
                else:
                    env.enable_line_numbers(env.buffer)
                env = resize_all(stdscr, env, True)
                screen, win = env.get_screen_for_current_mode()
                # rewrite = True
            elif key == curses.KEY_F6: # show/hide note highlight
                env.note_highlight = not env.note_highlight
                # rewrite = True
            elif key == curses.KEY_F7: # go to note management
                # env.update_viewing_data(win, buffer, report)
                env.enable_note_management()
                env.switch_to_next_mode()
                return env
            elif key == curses.KEY_F8: # reload from last save
                # env.update_viewing_data(win, buffer, report)
                exit_key = (curses.KEY_F8, "F8")
                if file_changes_are_saved(stdscr, env, RELOAD_FILE_WITHOUT_SAVING, exit_key):
                    env.buffer.lines = env.buffer.last_save.copy()
                    env.report.data = env.report.last_save.copy()
                # rewrite = True
                # rewrite_notes = True # TODO: if changed
            elif key == curses.KEY_F9:
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
                # curses.halfdelay(5)
                # while stdscr.getch() == curses.KEY_F9:
                    # pass
                # curses.cbreak(True)

            elif key == 27: # ESC TODO: manage file
                env.change_to_file_management()
            else:
                if env.file_edit_mode:
                    # ======================= EDIT FILE =======================
                    if key == curses.KEY_DC:
                        env.report = env.buffer.delete(win, env.report)
                        # rewrite = True # TODO: rewrite only lines with change
                        # rewrite_notes = True # TODO: if changed
                    elif key == curses.KEY_BACKSPACE: #
                        if (win.cursor.row, win.cursor.col) > (win.begin_y, win.begin_x):
                            win.left(env.buffer)
                            env.report = env.buffer.delete(win, env.report)
                            win.calculate_tab_shift(env.buffer, env.tab_size)
                            # rewrite = True # TODO: rewrite only lines with change
                            # rewrite_notes = True # TODO: if changed
                    elif key == curses.ascii.NL:
                        env.report = env.buffer.newline(win, env.report)
                        win.right(env.buffer, filter_on=env.content_filter_on())
                        win.calculate_tab_shift(env.buffer, env.tab_size)
                        # rewrite = True # TODO: rewrite only lines with change
                        # rewrite_notes = True # TODO: if changed
                    elif curses.ascii.isprint(key):
                        env.buffer.insert(win, chr(key))
                        win.right(env.buffer, filter_on=env.content_filter_on())
                        win.calculate_tab_shift(env.buffer, env.tab_size)
                        # rewrite = True # TODO: rewrite only lines with change
                        # rewrite_notes = True # TODO: if changed
                else:
                    # ======================= MANAGE FILE =======================
                    if curses.ascii.isprint(key):
                        char_key = chr(key)
                        if char_key == '\\': # go to filter management
                            env = filter_management(stdscr, screen, win, env)
                            # screen, win = env.get_screen_for_current_mode()
                            # env.update_viewing_data(win, buffer, report)
                            env.prepare_browsing_after_filter()
                            return env
                        elif char_key == '0': # add custom note
                            note_row, note_col = win.cursor.row, win.cursor.col - win.begin_x
                            # define specific highlight for current line which is related to the new note
                            env.specific_line_highlight = (note_row, curses.color_pair(NOTE_MGMT))

                            title = f"Enter new note at {note_row}:{note_col}"
                            env, text = get_user_input(stdscr, env, title=title)
                            screen, win = env.get_screen_for_current_mode()
                            curses.curs_set(1)
                            env.specific_line_highlight = None
                            if text is not None:
                                env.report.add_note(note_row, note_col, ''.join(text))

                        elif char_key in [str(i) for i in range(1,10)]: # add typical note
                            int_key = int(char_key)
                            if len(env.typical_notes) >= int_key:
                                str_text = env.typical_notes[int_key-1].text                              
                                note_row, note_col = win.cursor.row, win.cursor.col - win.begin_x
                                env.report.add_note(note_row, note_col, str_text)
                # ======================= CTRL KEYS =======================
                if curses.ascii.ismeta(key): # jump between notes in file
                    ctrl_key = curses.ascii.unctrl(key)
                    if ctrl_key == '7' or hex(key) == "0x237": # CTRL + UP: jump to prev note
                        if env.report and env.note_highlight:
                            prev_line = env.report.get_prev_line_with_note(win.cursor.row)
                            while win.cursor.row != prev_line:
                                win.up(env.buffer, use_restrictions=True)
                            win.calculate_tab_shift(env.buffer, env.tab_size)
                            # rewrite = True
                    elif ctrl_key == '^N' or hex(key) == "0x20e": # CTRL + DOWN: jump to next note
                        if env.report and env.note_highlight:
                            next_line = env.report.get_next_line_with_note(win.cursor.row)
                            while win.cursor.row != next_line:
                                win.down(env.buffer, filter_on=env.content_filter_on(), use_restrictions=True)
                            win.calculate_tab_shift(env.buffer, env.tab_size)
                            # rewrite = True
                elif curses.ascii.iscntrl(key):
                    ctrl_key = curses.ascii.unctrl(key)
                    if ctrl_key == '^L': # reload from original buffer
                        env.buffer.lines = env.buffer.original_buff.copy()
                        env.report.data = env.report.original_report.copy()
                        # rewrite = True
                        # rewrite_notes = True # TODO: if changed
        except Exception as err:
            log("viewing Exception | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env
