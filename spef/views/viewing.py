
import curses
import curses.ascii
import os
import traceback

from spef.controls.control import *
from spef.modules.bash import Bash_action
from spef.testing.tst import TST_FCE_DIR, TST_FCE_FILE, check_bash_functions_for_testing
from spef.testing.report import get_supported_data_for_report

from spef.utils.loading import *
from spef.utils.screens import *
from spef.utils.printing import *
from spef.utils.logger import *
from spef.utils.match import *
from spef.utils.file import copy_test_history_to_tmp
from spef.utils.reporting import get_path_relative_to_solution_dir

from spef.views.filtering import filter_management
from spef.views.help import show_help
from spef.views.input import get_user_input
from spef.views.user_logs import add_to_user_logs



def file_viewing(stdscr, env):
    screen, win = env.get_screen_for_current_mode()

    if not env.file_to_open or is_archive_file(env.file_to_open): # there is no file to open
        if env.show_tags and env.tags is not None:
            env.set_tag_mode()
        else:
            if env.show_logs:
                env.set_logs_mode()
            else:
                env.set_brows_mode()
        return env

    """ try load file content and tags """
    env, buffer, succ = load_buffer_and_tags(env)
    if not succ:
        env.set_file_to_open(None)
        env.set_brows_mode() # instead of exit mode
        return env

    # editing test file
    if os.path.basename(env.file_to_open) == TEST_FILE and env.cwd.proj:
        env.editing_test_file = True
        # copy test dir to history (if there is no other copy of this test with this version)
        succ = copy_test_history_to_tmp(env.cwd.proj.path, os.path.dirname(env.file_to_open))

    if os.path.basename(env.file_to_open) == REPORT_TEMPLATE and env.cwd.proj:
        env.editing_report_template = True
    else:
        env.editing_report_template = False


    """ try load code review to report  """
    report_already_loaded = False
    report = None
    if env.report is not None:
        report_file = get_report_file_name(buffer.path)
        if env.report.path == report_file:
            report_already_loaded = True
            report = env.report
    if not env.report or not report_already_loaded:
        # try get report for file in buffer
        orig_file_name = get_path_relative_to_solution_dir(buffer.path)
        report = load_report_from_file(buffer.path, orig_file_name=orig_file_name)
        env.report = report


    """ calculate line numbers """
    if env.line_numbers or env.start_with_line_numbers:
        env.start_with_line_numbers = False
        env.enable_line_numbers(buffer)

    if report is None:
        log("report is None (this will never execute probably)")
        env.set_exit_mode()
        return env


    env.buffer = buffer
    env.report = report
    rewrite_all_wins(env)
    curses.curs_set(1)
    rewrite = True
    rewrite_hint = True

    while True:
        """ print all screens """
        screen, win = env.get_screen_for_current_mode()
        if rewrite:
            rewrite_file(env, hint=rewrite_hint)

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
                env, rewrite, rewrite_hint, exit_view = run_function(stdscr, env, function, key)
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
    rewrite_hint = False

    # ======================= EXIT =======================
    if fce == EXIT_PROGRAM:
        if file_changes_are_saved(stdscr, env, add_to_user_logs):
            env.set_exit_mode()
            return env, rewrite, rewrite_hint, True
        rewrite = True
    # ======================= BASH =======================
    elif fce == BASH_SWITCH:
        hex_key = "{0:x}".format(key)
        env.bash_action = Bash_action()
        env.bash_action.set_exit_key(('0' if len(hex_key)%2 else '')+str(hex_key))
        env.bash_active = True
        return env, rewrite, rewrite_hint, True
    # ======================= FOCUS =======================
    elif fce == CHANGE_FOCUS:
        if env.show_tags:
            env.switch_to_next_mode()
            return env, rewrite, rewrite_hint, True
        else:
            if file_changes_are_saved(stdscr, env, add_to_user_logs):
                env.switch_to_next_mode()
                return env, rewrite, rewrite_hint, True
            rewrite = True
    # ======================= RESIZE =======================
    elif fce == RESIZE_WIN:
        env = resize_all(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
        rewrite_all_wins(env)
        curses.curs_set(1)
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
        show_help(stdscr, env)
        rewrite_all_wins(env)
        curses.curs_set(1)
    # ======================= SAVE FILE =======================
    elif fce == SAVE_FILE:
        save_buffer(stdscr, env, add_to_user_logs)
        rewrite_all_wins(env)
        curses.curs_set(1)
    # ======================= SHOW/HIDE TAGS =======================
    elif fce == SHOW_OR_HIDE_TAGS:
        env.show_tags = not env.show_tags
        screen, win = env.get_screen_for_current_mode()
        rewrite_all_wins(env)
        curses.curs_set(1)
    # ======================= LINE NUMBERS =======================
    elif fce == SHOW_OR_HIDE_LINE_NUMBERS:
        if env.line_numbers:
            env.disable_line_numbers()
        else:
            env.enable_line_numbers(env.buffer)
        rewrite = True
        rewrite_hint = True
    elif fce == SHOW_OR_HIDE_NOTE_HIGHLIGHT:
        env.note_highlight = not env.note_highlight
        rewrite = True
        rewrite_hint = True
    # ======================= SHOW NOTES =======================
    elif fce == OPEN_NOTE_MANAGEMENT:
        env.enable_note_management()
        # env.switch_to_next_mode()
        env.set_notes_mode()
        return env, rewrite, rewrite_hint, True
    elif fce == SHOW_TYPICAL_NOTES:
        # define specific highlight for current line which is related to the new note
        note_row, note_col = win.cursor.row, win.cursor.col - win.begin_x
        env.specific_line_highlight = (note_row, curses.color_pair(COL_NOTE_LIGHT))

        # show list of typical notes with indexes
        options = env.get_typical_notes_dict()
        custom_help = (None, "Typical notes:", options)
        env, key = show_help(stdscr, env, custom_help=custom_help, exit_key=[])
        curses.curs_set(1)
        env.specific_line_highlight = None

        # if key represents index of typical note, add this note to current line in file
        if curses.ascii.isprint(key):
            char_key = chr(key)
            if char_key in options.keys():
                str_text = options[char_key]
                note_row, note_col = win.cursor.row, win.cursor.col - win.begin_x
                env.report.add_note(note_row, note_col, str_text)
                save_report_to_file(env.report)
        rewrite_all_wins(env)
        curses.curs_set(1)
    # ==================== SHOW SUPPORTED DATA ====================
    elif fce == SHOW_SUPPORTED_DATA:
        if env.editing_test_file:
            # ==================== SHOW TEST FUNCTIONS ====================
            # show supported functions for 'dotest.sh' while user is writing/editing some test
            # show list of implemented functions for testing
            try:
                check_bash_functions_for_testing(env.cwd.proj.path)
                bash_file = os.path.join(env.cwd.proj.path, TESTS_DIR, TST_FCE_DIR, TST_FCE_FILE)
                options = env.get_supported_test_functions(bash_file)
                custom_help = (None, "Supported functions:", options)
                env, key = show_help(stdscr, env, custom_help=custom_help, exit_key=[])
                curses.curs_set(1)
                rewrite_all_wins(env)
                curses.curs_set(1)
            except Exception as err:
                log("show test functions | "+str(err))
        elif env.editing_report_template:
            # =============== SHOW DATA FOR REPORT TEMPLATE ===============
            # show supported data for 'report_template.j2' while user is creating report template
            try:
                options = get_supported_data_for_report()
                custom_help = (None, "Supported data:", options)
                env, key = show_help(stdscr, env, custom_help=custom_help, exit_key=[])
                rewrite_all_wins(env)
                curses.curs_set(1)
            except Exception as err:
                log("show report template data | "+str(err))
    # ======================= NOTES JUMP =======================
    elif fce == GO_TO_PREV_NOTE:
        if env.note_highlight:
            old_shifts = win.row_shift, win.col_shift # get old shifts
            prev_line = env.report.get_prev_line_with_note(win.cursor.row)
            while win.cursor.row != prev_line:
                win.up(env.buffer, use_restrictions=True)
            win.calculate_tab_shift(env.buffer, env.tab_size)
            env.update_win_for_current_mode(win)
            rewrite = (old_shifts != (win.row_shift, win.col_shift)) # rewrite if shifts changed
    elif fce == GO_TO_NEXT_NOTE:
        if env.note_highlight:
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
        env.report.data = env.report.original_report.copy()
        while win.cursor.row > len(env.buffer):
            win.up(env.buffer, use_restrictions=False)
        win.calculate_tab_shift(env.buffer, env.tab_size)
        if win.cursor.col > len(env.buffer[win.cursor.row - win.begin_y])+win.begin_x:
            win.cursor.col = win.begin_x
        rewrite = True
    elif fce == RELOAD_FILE_FROM_LAST_SAVE:
        if file_changes_are_saved(stdscr, env, add_to_user_logs, warning=RELOAD_FILE_WITHOUT_SAVING):
            env.buffer.lines = env.buffer.last_save.copy()
            env.report.data = env.report.last_save.copy()
            while win.cursor.row > len(env.buffer):
                win.up(env.buffer, use_restrictions=False)
            win.calculate_tab_shift(env.buffer, env.tab_size)
            if win.cursor.col > len(env.buffer[win.cursor.row - win.begin_y])+win.begin_x:
                win.cursor.col = win.begin_x
        rewrite = True
    else:
        # ======================= EDIT FILE =======================
        if env.file_edit_mode:
            # ======================= DELETE =======================
            if fce == DELETE_CHAR:
                old_len = len(env.buffer)
                # delete char and update report
                env.report = env.buffer.delete(win, env.report)
                # check if its necessary to rewrite the whole window or just one line
                if old_len == len(env.buffer):
                    env.update_win_for_current_mode(win)
                    rewrite_one_line_in_file(env, win.cursor.row)
                else:
                    rewrite = True
                # update the total number of lines
                if env.line_numbers:
                    env.enable_line_numbers(env.buffer)
            # ======================= BACKSPACE =======================
            elif fce == BACKSPACE_CHAR:
                old_len = len(env.buffer)
                # delete char and update report
                if (win.cursor.row, win.cursor.col) > (win.begin_y, win.begin_x):
                    win.left(env.buffer)
                    env.report = env.buffer.delete(win, env.report)
                    win.calculate_tab_shift(env.buffer, env.tab_size)
                # check if its necessary to rewrite the whole window or just one line
                if old_len == len(env.buffer):
                    env.update_win_for_current_mode(win)
                    rewrite_one_line_in_file(env, win.cursor.row)
                else:
                    rewrite = True
                # update the total number of lines
                if env.line_numbers:
                    env.enable_line_numbers(env.buffer)
            # ======================= NEW LINE =======================
            elif fce == PRINT_NEW_LINE:
                # add new line
                env.report = env.buffer.newline(win, env.report)
                win.right(env.buffer, filter_on=env.content_filter_on())
                win.calculate_tab_shift(env.buffer, env.tab_size)
                rewrite = True
                # update the total number of lines
                if env.line_numbers:
                    env.enable_line_numbers(env.buffer)
            # ======================= PRINT CHAR =======================
            elif fce == PRINT_CHAR:
                old_len = len(env.buffer)
                # print char
                if key is not None:
                    env.buffer.insert(win, chr(key))
                    win.right(env.buffer, filter_on=env.content_filter_on())
                    win.calculate_tab_shift(env.buffer, env.tab_size)
                # check if its necessary to rewrite the whole window or just one line
                if old_len == len(env.buffer):
                    env.update_win_for_current_mode(win)
                    rewrite_one_line_in_file(env, win.cursor.row)
                else:
                    rewrite = True
                # update the total number of lines
                if env.line_numbers:
                    env.enable_line_numbers(env.buffer)
            # ======================= EDIT -> MANAGE =======================
            elif fce == SET_MANAGE_FILE_MODE:
                env.change_to_file_management()
        else:
            # ======================= FILTER =======================
            if fce == FILTER:
                env = filter_management(stdscr, screen, win, env)
                if env.is_exit_mode() or env.is_brows_mode():
                    return env, rewrite, rewrite_hint, True
                rewrite = True
            # ======================= MANAGE -> EDIT =======================
            elif fce == SET_EDIT_FILE_MODE:
                env.change_to_file_edit_mode()
            # ======================= ADD NOTES =======================
            elif fce == ADD_CUSTOM_NOTE:
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
                    save_report_to_file(env.report)
                rewrite_all_wins(env)
                curses.curs_set(1)
            elif fce == ADD_TYPICAL_NOTE:
                options = env.get_typical_notes_dict()
                char_key = chr(key)
                if char_key in options.keys():
                    str_text = options[char_key]
                    note_row, note_col = win.cursor.row, win.cursor.col - win.begin_x
                    env.report.add_note(note_row, note_col, str_text)
                    save_report_to_file(env.report)
                rewrite_all_wins(env)
                curses.curs_set(1)

    env.update_win_for_current_mode(win)
    return env, rewrite, rewrite_hint, False

