import curses
import curses.ascii
import yaml
import os


from views.help import show_help

from modules.buffer import Tags, UserInput

from views.menu import brows_menu

from utils.loading import save_report_to_file
from utils.input import get_user_input
from utils.screens import *
from utils.printing import *
from utils.logger import *
from utils.coloring import *


def notes_management(stdscr, env):
    curses.curs_set(0)
    screen, win = env.get_screen_for_current_mode()

    report = env.report
    if report is None:
        log("unexpected error in note management - there is no report in env")
        env.disable_note_management()
        env.set_view_mode()
        return env


    while True:
        """ print notes """
        env.update_report_data(win, report)
        rewrite_all_wins(stdscr, env)


        key = stdscr.getch()
        try:
            # ======================= EXIT =======================
            if key == curses.ascii.ESC: # exit note management
                env.disable_note_management()
                env.update_report_data(win, report)
                env.switch_to_next_mode()
                save_report_to_file(report)
                return env
            if key == curses.KEY_F10: # exit program
                env.disable_note_management()
                env.update_report_data(win, report)
                env.set_exit_mode()
                save_report_to_file(report)
                return env
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                env.update_report_data(win, report)
                env.switch_to_next_mode()
                return env
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                env = resize_all(stdscr, env)
                screen, win = env.get_screen_for_current_mode()
                curses.curs_set(0)
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(report, use_restrictions=False)
            elif key == curses.KEY_DOWN:
                win.down(report, filter_on=env.tag_filter_on(), use_restrictions=False)
            # ======================= F KEYS =======================
            elif key == curses.KEY_F1: # user help
                env = show_help(stdscr, env)
                screen, win = env.get_screen_for_current_mode()
                curses.curs_set(0)
            elif key == curses.KEY_F2: # edit current note
                current_note = report.data[win.cursor.row]
                user_input = UserInput()
                user_input.text = list(current_note.text)

                # define specific highlight for current line which is related to the new note
                env.specific_line_highlight = (current_note.row, curses.color_pair(NOTE_MGMT))

                title = "Edit note:"
                env, text = get_user_input(stdscr, env, title=title, user_input=user_input)
                env.specific_line_highlight = None
                curses.curs_set(0)
                if text is not None:
                    report.data[win.cursor.row].text = ''.join(text)

            elif key == curses.KEY_F3: # create new note
                file_win = env.windows.edit if env.edit_allowed else env.windows.view
                note_row, note_col = file_win.cursor.row, file_win.cursor.col - file_win.begin_x
                current_note_row = report.data[win.cursor.row].row
                current_note_col = report.data[win.cursor.row].col

                # define specific highlight for current line which is related to the new note
                env.specific_line_highlight = (note_row, curses.color_pair(NOTE_MGMT))

                title = "Enter new note:"
                env, text = get_user_input(stdscr, env, title=title)
                env.specific_line_highlight = None
                curses.curs_set(0)
                if text is not None:
                    report.add_note(note_row, note_col, ''.join(text))

                    """ move cursor down if new note is lower then current item (current cursor position) """
                    if note_row < current_note_row or (note_row == current_note_row and note_col < current_note_col):
                        win.down(report, filter_on=env.tag_filter_on(), use_restrictions=False)

            elif key == curses.KEY_F4: # insert note from typical notes
                file_win = env.windows.edit if env.edit_allowed else env.windows.view
                note_row, note_col = file_win.cursor.row, file_win.cursor.col - file_win.begin_x
                current_note_row = report.data[win.cursor.row].row
                current_note_col = report.data[win.cursor.row].col

                # define specific highlight for current line which is related to the new note
                env.specific_line_highlight = (note_row, curses.color_pair(NOTE_MGMT))

                title = "Select from typical notes: "
                color = curses.color_pair(GREEN_COL)
                menu_options = [note.text for note in env.typical_notes]
                env, option_idx = brows_menu(stdscr, env, menu_options, color=color, title=title)
                env.specific_line_highlight = None
                curses.curs_set(0)
                if option_idx is not None:
                    if len(env.typical_notes) >= option_idx:
                        str_text = env.typical_notes[option_idx].text
                        report.add_note(note_row, note_col, str_text)

                        """ move cursor down if new note is lower then current item (current cursor position) """
                        if note_row < current_note_row or (note_row == current_note_row and note_col < current_note_col):
                            win.down(report, filter_on=env.tag_filter_on(), use_restrictions=False)


            elif key == curses.KEY_F5: # go to current note in file
                current_note = report.data[win.cursor.row]
                env.update_report_data(win, report)
                env.switch_to_next_mode()
                _, view_win = env.get_screen_for_current_mode()
                if current_note.row < view_win.cursor.row:
                    while current_note.row != view_win.cursor.row:
                        view_win.up(env.buffer, use_restrictions=True)
                else:
                    while current_note.row != view_win.cursor.row:
                        view_win.down(env.buffer, filter_on=env.content_filter_on(), use_restrictions=True)
                return env
            elif key == curses.KEY_F6: # save note as typical
                current_note = report.data[win.cursor.row]
                if current_note.is_typical(env):
                    current_note.remove_from_typical(env)
                else:
                    current_note.set_as_typical(env)
            elif key == curses.KEY_F8: # delete note
                if len(report.data) >= win.cursor.row:
                    del report.data[win.cursor.row]
                    win.up(report, use_restrictions=False)
        except Exception as err:
            log("note management | "+str(err))
            env.set_exit_mode()
            return env
