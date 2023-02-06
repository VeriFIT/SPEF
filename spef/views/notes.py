import curses
import curses.ascii
import traceback

import spef.controls.functions as func
from spef.controls.control import get_function_for_key
from spef.modules.buffer import UserInput
from spef.modules.bash import Bash_action
from spef.utils.loading import save_report_to_file
from spef.utils.screens import resize_all
from spef.utils.printing import rewrite_all_wins
from spef.utils.logger import log
from spef.utils.coloring import COL_NOTE_LIGHT
from spef.views.input import get_user_input
from spef.views.help import show_help


def notes_management(stdscr, env):
    curses.curs_set(0)
    screen, win = env.get_screen_for_current_mode()

    if env.report is None:
        log("unexpected error in note management - there is no report in env")
        env.disable_note_management()
        env.set_view_mode()
        return env

    file_win = env.windows.view_up if env.show_tags else env.windows.view
    note_row, note_col = file_win.cursor.row, file_win.cursor.col - file_win.begin_x

    # define specific highlight for current line which is related to the new note
    env.specific_line_highlight = (note_row, curses.color_pair(COL_NOTE_LIGHT))

    while True:
        """print notes"""
        rewrite_all_wins(env)

        key = stdscr.getch()

        try:
            function = get_function_for_key(env, key)
            if function is not None:
                env, exit_program = run_function(
                    stdscr, env, function, key, (note_row, note_col)
                )
                if exit_program:
                    env.specific_line_highlight = None
                    return env
        except Exception as err:
            log("note management | " + str(err) + " | " + str(traceback.format_exc()))
            env.set_exit_mode()
            return env


""" implementation of functions for note management """


def run_function(stdscr, env, fce, key, line):
    screen, win = env.get_screen_for_current_mode()
    note_row, note_col = line

    # ==================== EXIT PROGRAM ====================
    if fce == func.EXIT_PROGRAM:
        env.disable_note_management()
        env.set_exit_mode()
        save_report_to_file(env.report)
        return env, True
    # ======================= BASH =======================
    elif fce == func.BASH_SWITCH:
        hex_key = "{0:x}".format(key)
        env.bash_action = Bash_action()
        env.bash_action.set_exit_key(("0" if len(hex_key) % 2 else "") + str(hex_key))
        env.bash_active = True
        return env, True
    # ================ EXIT NOTE MANAGEMENT ================
    elif fce == func.EXIT_NOTES:
        env.disable_note_management()
        env.switch_to_next_mode()
        save_report_to_file(env.report)
        return env, True
    # ======================= FOCUS =======================
    elif fce == func.CHANGE_FOCUS:
        env.switch_to_next_mode()
        return env, True
    # ======================= RESIZE =======================
    elif fce == func.RESIZE_WIN:
        env = resize_all(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
    # ======================= ARROWS =======================
    elif fce == func.CURSOR_UP:
        win.up(env.report, use_restrictions=False)
    elif fce == func.CURSOR_DOWN:
        win.down(env.report, filter_on=env.tag_filter_on(), use_restrictions=False)
    # ===================== SHOW HELP ======================
    elif fce == func.SHOW_HELP:
        show_help(stdscr, env)
        curses.curs_set(0)
    # ===================== EDIT NOTE =====================
    elif fce == func.EDIT_NOTE:
        if len(env.report.data) > 0 and len(env.report.data) >= win.cursor.row:
            current_note = env.report.data[win.cursor.row]
            user_input = UserInput()
            user_input.text = list(current_note.text)

            # define specific highlight for current line which is related to the new note
            old_highlight = env.specific_line_highlight
            env.specific_line_highlight = (
                current_note.row,
                curses.color_pair(COL_NOTE_LIGHT),
            )

            title = f"Edit note at {current_note.row}:{current_note.col}"
            env, text = get_user_input(stdscr, env, title=title, user_input=user_input)
            screen, win = env.get_screen_for_current_mode()
            curses.curs_set(0)
            env.specific_line_highlight = old_highlight
            if text is not None:
                env.report.data[win.cursor.row].text = "".join(text)
    # ================== CREATE NEW NOTE ==================
    elif fce == func.ADD_CUSTOM_NOTE:
        title = f"Enter new note at {note_row}:{note_col}"
        env, text = get_user_input(stdscr, env, title=title)
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
        if text is not None:
            """move cursor down if new note is lower then current item (current cursor position)"""
            if len(env.report.data) > 0:
                current_note_row = env.report.data[win.cursor.row].row
                current_note_col = env.report.data[win.cursor.row].col
                if note_row < current_note_row or (
                    note_row == current_note_row and note_col < current_note_col
                ):
                    win.down(
                        env.report,
                        filter_on=env.tag_filter_on(),
                        use_restrictions=False,
                    )

            """ add note to report """
            env.report.add_note(note_row, note_col, "".join(text))
            save_report_to_file(env.report)
    # ================ INSERT TYPICAL NOTE ================
    elif fce == func.ADD_TYPICAL_NOTE:
        options = env.get_typical_notes_dict()
        char_key = chr(key)
        if char_key in options.keys():
            """move cursor down if new note is lower then current item (current cursor position)"""
            if len(env.report.data) > 0:
                current_note_row = env.report.data[win.cursor.row].row
                current_note_col = env.report.data[win.cursor.row].col
                if note_row < current_note_row or (
                    note_row == current_note_row and note_col < current_note_col
                ):
                    win.down(
                        env.report,
                        filter_on=env.tag_filter_on(),
                        use_restrictions=False,
                    )

            """ add note to report """
            str_text = options[char_key]
            env.report.add_note(note_row, note_col, str_text)
            save_report_to_file(env.report)
    elif fce == func.SHOW_TYPICAL_NOTES:
        # show list of typical notes with indexes
        options = env.get_typical_notes_dict()
        custom_help = (None, "Typical notes:", options)
        env, key = show_help(stdscr, env, custom_help=custom_help, exit_key=[])
        curses.curs_set(0)

        # if key represents index of typical note, add this note to current line in file
        if curses.ascii.isprint(key):
            char_key = chr(key)
            if char_key in options.keys():
                """move cursor down if new note is lower then current item (current cursor position)"""
                if len(env.report.data) > 0:
                    current_note_row = env.report.data[win.cursor.row].row
                    current_note_col = env.report.data[win.cursor.row].col
                    if note_row < current_note_row or (
                        note_row == current_note_row and note_col < current_note_col
                    ):
                        win.down(
                            env.report,
                            filter_on=env.tag_filter_on(),
                            use_restrictions=False,
                        )

                """ add note to report """
                str_text = options[char_key]
                env.report.add_note(note_row, note_col, str_text)
                save_report_to_file(env.report)
    # ==================== GO TO NOTE ====================
    elif fce == func.GO_TO_NOTE:
        if len(env.report.data) > 0:
            current_note = env.report.data[win.cursor.row]
            env.switch_to_next_mode()
            _, view_win = env.get_screen_for_current_mode()
            if current_note.row < view_win.cursor.row:
                while current_note.row != view_win.cursor.row:
                    view_win.up(env.buffer, use_restrictions=True)
            else:
                while current_note.row != view_win.cursor.row:
                    view_win.down(
                        env.buffer,
                        filter_on=env.content_filter_on(),
                        use_restrictions=True,
                    )
            return env, True
    # ================== SAVE AS TYPICAL ==================
    elif fce == func.SAVE_AS_TYPICAL_NOTE:
        if len(env.report.data) > 0:
            current_note = env.report.data[win.cursor.row]
            if current_note.is_typical(env):
                current_note.remove_from_typical(env)
            else:
                current_note.set_as_typical(env)
    # ==================== DELETE NOTE ====================
    elif fce == func.DELETE_NOTE:
        if len(env.report.data) > 0 and len(env.report.data) >= win.cursor.row:
            del env.report.data[win.cursor.row]
            if len(env.report.data) <= win.cursor.row:
                win.up(env.report, use_restrictions=False)
                save_report_to_file(env.report)

    env.update_win_for_current_mode(win)
    return env, False
