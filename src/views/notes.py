import curses
import curses.ascii
import yaml
import os


from views.help import show_help

from modules.buffer import Tags, UserInput

from utils.loading import load_tags_from_file
from utils.input import get_user_input
from utils.screens import *
from utils.printing import *
from utils.logger import *



def notes_management(stdscr, env):
    curses.curs_set(0)
    screen, win = env.get_screen_for_current_mode()

    report = env.report
    if report is None:
        log("unexpected error in note manatemeng - there is no report in env")
        env.disable_note_management()
        env.set_view_mode()
        return env


    while True:
        """ print notes """
        env.update_report_data(win, report)
        rewrite_all_wins(env)


        key = stdscr.getch()
        try:
            # ======================= EXIT =======================
            if key in (curses.ascii.ESC, curses.KEY_F10): # exit note manatement
                env.disable_note_management()
                env.update_report_data(win, report)
                env.switch_to_next_mode()
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
                pass
                # title = "Edit note:"
                # env, text = get_user_input(stdscr, env, title=title)
                # curses.curs_set(0)
                # if text is not None:
                    # log(text)

            elif key == curses.KEY_F3: # create new note
                # TODO !!! zvyrazni sa riadok kde sa ide aktualne vo file editore pridat poznamka !!!
                file_cursor = env.windows.edit.cursor if env.edit_allowed else env.windows.view.cursor
                line, col = file_cursor.row, file_cursor.col
                # line, col = file_cursor.row-1, file_cursor.col
                # report.add_note(line, col, text):

                # env.note_edit = True
                env.specific_line_highlight = (line, curses.color_pair(NOTE_MGMT))
                title = "Enter new note:"
                env, text = get_user_input(stdscr, env, title=title)
                # env.note_edit = False
                env.specific_line_highlight = None

                curses.curs_set(0)
                if text is not None:
                    log(text)
            # elif key == curses.KEY_F4: # insert note from typical notes
            # elif key == curses.KEY_F5: # go to current note in file
            # elif key == curses.KEY_F6: # save note as typical
            # elif key == curses.KEY_F8: # delete note
                # if report:
                    # report.delete_notes_on_line(win.cursor.row)

        except Exception as err:
            log("note management | "+str(err))
            env.set_exit_mode()
            return env
