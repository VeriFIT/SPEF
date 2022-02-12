
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


def file_viewing(stdscr, conf):
    curses.curs_set(1) # set cursor as visible
    screen, win = conf.get_screen_for_current_mode()


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
        """ print all screens """
        conf.update_viewing_data(win, buffer, report)
        rewrite_all_wins(conf)

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
                save_report_to_file(report)
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
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                conf.update_viewing_data(win, buffer, report)
                if conf.edit_allowed:
                    if file_changes_are_saved(stdscr, conf):
                        conf.set_brows_mode()
                        return conf
                else:
                    conf.set_tag_mode()
                    return conf
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(buffer, use_restrictions=True)
                win.calculate_tab_shift(buffer)
            elif key == curses.KEY_DOWN:
                win.down(buffer, filter_on=conf.content_filter_on(), use_restrictions=True)
                win.calculate_tab_shift(buffer)
            elif key == curses.KEY_LEFT:
                win.left(buffer)
                win.calculate_tab_shift(buffer)
            elif key == curses.KEY_RIGHT:
                win.right(buffer, filter_on=conf.content_filter_on())
                win.calculate_tab_shift(buffer)
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen, win = conf.get_screen_for_current_mode()
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
                    elif key == curses.KEY_F1: # help
                        conf = show_help(stdscr, conf)
                        screen, win = conf.get_screen_for_current_mode()
                        curses.curs_set(1)
                    elif key == curses.KEY_F2: # save file
                        save_buffer(conf.file_to_open, buffer, report)
                    elif key == curses.KEY_F3: # change to view/tag mode
                        conf.update_viewing_data(win, buffer, report)
                        if file_changes_are_saved(stdscr, conf):
                            conf.disable_file_edit()
                            return conf
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
                        conf = filter_management(stdscr, screen, win, conf)
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
                    if key == curses.KEY_F1: # help
                        show_help(stdscr, conf)
                        curses.curs_set(1)
                    elif key == curses.KEY_F4: # change to edit mode
                        conf.enable_file_edit()
                        return conf
                    elif key == curses.KEY_F9: # set filter
                        conf = filter_management(stdscr, screen, win, conf)
                        screen, win = conf.get_screen_for_current_mode()
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

