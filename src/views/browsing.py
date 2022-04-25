
import curses
import curses.ascii
import os
import shutil
import shlex
import traceback
import tarfile
import zipfile

from controls.control import *
from controls.functions import *

from views.filtering import filter_management
from views.help import show_help
from views.menu import brows_menu
from views.input import get_user_input

from modules.directory import Directory
from modules.project import Project
from modules.bash import Bash_action

from utils.loading import *
from utils.screens import *
from utils.printing import *
from utils.logger import *
from utils.reporting import *
from utils.match import *
from utils.file import *
from utils.history import history_test_removed

from testing.tst import *
from testing.report import generate_report_from_template


def get_directory_content(env):
    if env.filter_not_empty():
        files = env.filter.aggregate_files if env.filter.aggregate else env.filter.files
        dirs = env.filter.aggregate_dirs if env.filter.aggregate else []
        cwd = Directory(env.filter.root, dirs, files)
        cwd.get_proj_conf()
        return cwd

    path = os.getcwd() # current working directory path
    files, dirs = [], []
    for dir_path, dir_names, file_names in os.walk(path):
        if env.show_cached_files:
            files.extend(file_names)
        else:
            for file_name in file_names:
                if not file_name.endswith((REPORT_SUFFIX, TAGS_SUFFIX)):
                    files.append(file_name)
        dirs.extend(dir_names)
        break
    dirs.sort()
    files.sort()
    cwd = Directory(path, dirs, files)
    cwd.get_proj_conf()
    cwd.get_dirs_info(env)
    return cwd



def directory_browsing(stdscr, env):
    curses.curs_set(0)
    screen, win = env.get_screen_for_current_mode()

    env.cwd = get_directory_content(env)

    while True:
        screen, win = env.get_screen_for_current_mode()

        """ try to load buffer and tag for current file in directory structure """
        idx = win.cursor.row
        if env.quick_view and idx < len(env.cwd):
            dirs_and_files = env.cwd.get_all_items()
            # if its file, show its content and tags
            if idx >= len(env.cwd.dirs) and len(dirs_and_files)>idx:
                selected_file = os.path.join(env.cwd.path, dirs_and_files[idx])
                # if its archive file, show its content (TODO)
                if is_archive_file(selected_file):
                    pass
                else:
                    old_file_to_open = env.file_to_open
                    env.set_file_to_open(selected_file)
                    env, buffer, succ = load_buffer_and_tags(env) # try to load file
                    if not succ: # couldnt load buffer and/or fags for current file
                        env.set_file_to_open(old_file_to_open)
                        env.set_brows_mode() # continue to browsing without showing file content (instead of exit mode)
                    else:
                        """ set line numbers """
                        if env.line_numbers or env.start_with_line_numbers:
                            env.start_with_line_numbers = False
                            env.enable_line_numbers(buffer)
            # if its project directory, show project info and test results
            else:
                if env.cwd.proj is not None and len(dirs_and_files)>idx: # current working directory is a project subdirectory (ex: "proj1/")
                    # env.cwd.proj
                    selected_dir =  os.path.join(env.cwd.path, dirs_and_files[idx])
                    env = load_tags_if_changed(env, selected_dir)
                    # if proj.match_solution_id(selected_dir): # selected item is solution directory (ex: "proj1/xlogin00/")
                        # if proj.quick_view_file in selected_dir.files():
                        #    show_file_and_tags(proj.quick_view_file)
                    # elif proj.is_solution_subdirectory(selected_dir): # selected item is inside some solution subdirectory (ex: "proj1/xlogin00/dir/")
                        # if proj.is_test_directory(selected_dir): # is test directory == 
                        #    tests_conf = load_tests_from_conf_file(selected_dir)
                        #    show_file()
                        #    show_test_tags()

                pass # TODO: show project info and test tags
            env.update_win_for_current_mode(win)


        """ print all screens """
        rewrite_all_wins(env)


        key = stdscr.getch()

        try:
            function = get_function_for_key(env, key)
            if function is not None:
                env, exit_program = run_function(stdscr, env, function, key)
                if exit_program:
                    return env

        except Exception as err:
            log("browsing with quick view | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env



""" implementation of functions for directory browsing """
def run_function(stdscr, env, fce, key):
    screen, win = env.get_screen_for_current_mode()

    # ======================= EXIT =======================
    if fce == EXIT_PROGRAM:
        env.set_exit_mode()
        return env, True
    # ======================= BASH =======================
    elif fce == BASH_SWITCH:
        hex_key = "{0:x}".format(key)
        env.bash_action = Bash_action()
        env.bash_action.set_exit_key(('0' if len(hex_key)%2 else '')+str(hex_key))
        env.bash_active = True
        return env, True
    # ======================= FOCUS =======================
    elif fce == CHANGE_FOCUS:
        env.switch_to_next_mode()
        return env, True
    # ==================== FOCUS TO TAGS ====================
    elif fce == GO_TO_TAGS:
        if env.show_tags:
            env.set_tag_mode()
            return env, True
    # ======================= RESIZE =======================
    elif fce == RESIZE_WIN:
        env = resize_all(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
    # ======================= ARROWS =======================
    elif fce == CURSOR_UP:
        win.up(env.cwd, use_restrictions=False)
    elif fce == CURSOR_DOWN:
        win.down(env.cwd, filter_on=env.path_filter_on(), use_restrictions=False)
    elif fce == CURSOR_RIGHT:
        idx = win.cursor.row
        if not env.filter_not_empty() and idx < len(env.cwd.dirs):
            """ go to subdirectory """
            os.chdir(os.path.join(env.cwd.path, env.cwd.dirs[idx]))
            env.cwd = get_directory_content(env)
            win.reset(0,0) # set cursor on first position (first item)
    elif fce == CURSOR_LEFT:
        current_dir = os.path.basename(env.cwd.path) # get directory name
        if not env.filter_not_empty() and current_dir: # if its not root
            """ go to parent directory """
            os.chdir('..')
            env.cwd = get_directory_content(env)
            win.reset(0,0)
            """ set cursor position to prev directory """
            dir_position = env.cwd.dirs.index(current_dir) # find position of prev directory
            if dir_position:
                for i in range(0, dir_position):
                    win.down(env.cwd, filter_on=env.path_filter_on(), use_restrictions=False)
    # ======================= SHOW HELP =======================
    elif fce == SHOW_HELP:
        show_help(stdscr, env)
        curses.curs_set(0)
    # ======================= OPEN MENU =======================
    elif fce == OPEN_MENU:
        idx = win.cursor.row
        dirs_and_files = env.cwd.get_all_items()
        if len(dirs_and_files)>idx:
            selected_item = os.path.join(env.cwd.path, dirs_and_files[idx]) # selected item
        else:
            selected_item = env.cwd.path

        # show menu with functions
        in_proj_dir = is_in_project_dir(selected_item)
        in_solution_dir = is_in_solution_dir(env.cwd.proj.solution_id, selected_item) if env.cwd.proj is not None else False
        is_test_dir = is_testcase_dir(env.cwd.path) or is_testcase_dir(selected_item)
        menu_functions = get_menu_functions(in_proj_dir, in_solution_dir, is_test_dir)

        title = "Select function from menu: "
        menu_options = [key for key in menu_functions]
        env, option_idx = brows_menu(stdscr, env, menu_options, keys=True, title=title)
        if env.is_exit_mode():
            return env, True
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)

        # execute selected function
        if option_idx is not None:
            for i, key in enumerate(menu_functions):
                if i == option_idx:
                    rewrite_all_wins(env)
                    function = menu_functions[key]
                    env, exit_program = run_menu_function(stdscr, env, function, key)
                    if exit_program:
                        return env, True
    # ======================= QUICK VIEW =======================
    elif fce == QUICK_VIEW_ON_OFF:
        env.quick_view = not env.quick_view
    # ====================== CACHED FILES ======================
    elif fce == SHOW_OR_HIDE_CACHED_FILES:
        env.show_cached_files = not env.show_cached_files
        env.cwd = get_directory_content(env)
    # ======================= OPEN FILE =======================
    elif fce == OPEN_FILE:
        idx = win.cursor.row
        dirs_and_files = env.cwd.get_all_items()
        if len(dirs_and_files)>idx:
            selected_item = os.path.join(env.cwd.path, dirs_and_files[idx])
            if os.path.isfile(selected_item):
                env.set_file_to_open(os.path.join(env.cwd.path, dirs_and_files[idx]))
                env.switch_to_next_mode()
                return env, True
    # ======================= DELETE FILE =======================
    elif fce == DELETE_FILE:
        idx = win.cursor.row
        dirs_and_files = env.cwd.get_all_items()
        if len(dirs_and_files)>idx:
            file_to_delete = os.path.join(env.cwd.path, dirs_and_files[idx])
            if os.path.exists(file_to_delete) and os.path.isfile(file_to_delete):
                os.remove(file_to_delete)
                win.up(env.cwd, use_restrictions=False)
                # actualize current working directory
                env.cwd = get_directory_content(env)
    # ======================= FILTER =======================
    elif fce == FILTER:
        env = filter_management(stdscr, screen, win, env)
        if env.is_exit_mode():
            return env, True
        screen, win = env.get_screen_for_current_mode()
        # actualize current working directory
        env.cwd = get_directory_content(env)
        win.reset(0,0)
        curses.curs_set(0)

    env.update_win_for_current_mode(win)
    return env, False



def try_get_solution_from_selected_item(env, idx):
    solution = None
    dirs_and_files = env.cwd.get_all_items()
    if env.cwd.proj is not None and len(dirs_and_files)>idx:
        selected_item = dirs_and_files[idx]
        if selected_item in env.cwd.proj.solutions:
            solution = env.cwd.proj.solutions[selected_item]
        else:
            solution_dir = get_root_solution_dir(env.cwd.proj.solution_id, env.cwd.path)
            if solution_dir is not None:
                solution_id = os.path.basename(solution_dir)
                if solution_id in env.cwd.proj.solutions:
                    solution = env.cwd.proj.solutions[solution_id]
    return solution


def run_menu_function(stdscr, env, fce, key):
    screen, win = env.get_screen_for_current_mode()

    # ======================= ADD PROJECT =======================
    if fce == ADD_PROJECT:
        if env.cwd.proj is not None:
            return env, False
        env = create_project(env)
        env.cwd = get_directory_content(env)
    # ======================= CREATE DIR =======================
    elif fce == CREATE_DIR:
        # get name for new dir
        title = "Enter a name for new directory:"
        env, dir_name = get_user_input(stdscr, env, title=title)
        if env.is_exit_mode():
            return env, True
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
        if dir_name is not None:
            dir_name = ''.join(dir_name).strip()
            new_dir = os.path.join(env.cwd.path, dir_name)
            if os.path.exists(new_dir) and os.path.isdir(new_dir):
                log(f"create dir | directory {new_dir} already exists")
            else:
                os.mkdir(new_dir)
                env.cwd = get_directory_content(env)
    # ======================= CREATE FILE =======================
    elif fce == CREATE_FILE:
        # get name for new file
        title = "Enter a name for new file:"
        env, file_name = get_user_input(stdscr, env, title=title)
        if env.is_exit_mode():
            return env, True
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
        if file_name is not None:
            file_name = ''.join(file_name).strip()
            new_file = os.path.join(env.cwd.path, file_name)
            if os.path.exists(new_file) and os.path.isfile(new_file):
                log(f"create file | file {new_file} already exists")
            else:
                with open(new_file, 'w+'): pass
                env.cwd = get_directory_content(env)
    # ====================== EDIT PROJ CONFIG ======================
    elif fce == EDIT_PROJ_CONF:
        if env.cwd.proj is not None:
            env.set_file_to_open(os.path.join(env.cwd.proj.path, PROJ_CONF_FILE))
            env.switch_to_next_mode()
            return env, True
    # ============================ EXPAND ===========================
    elif fce == EXPAND_ALL_SOLUTIONS: # ALL STUDENTS
        if env.cwd.proj is not None:
            solutions, problem_files = get_solution_archives(env)
            problem_solutions = extract_archives(solutions)
            problem_solutions.update(problem_files)
            if problem_solutions:
                log("extract | problem archives: "+str(problem_solutions))
            env.cwd = get_directory_content(env)
            env.cwd.proj.reload_solutions()
    # ============================ RENAME ===========================
    elif fce == RENAME_ALL_SOLUTIONS: # ALL STUDENTS
        if env.cwd.proj is not None:
            if env.cwd.proj.sut_required == "":
                log("rename all solutions | there is no defined sut_required in proj config")
            else:
                ok, renamed, fail = rename_solutions(env.cwd.proj)
                log("students with correctly named solution file: "+str(ok))
                log("students with wrong named solution file: "+str(renamed))
                log("students with no supported extention of solution file: "+str(fail))
    # ====================== EXPAND AND RENAME ======================
    elif fce == EXPAND_AND_RENAME_SOLUTION: # on solution dir
        idx = win.cursor.row
        dirs_and_files = env.cwd.get_all_items()
        if env.cwd.proj is not None and len(dirs_and_files)>idx:
            path = os.path.join(env.cwd.path, dirs_and_files[idx]) # selected item
            if is_solution_file(env.cwd.proj.solution_id, path):
                if not is_archive_file(path):
                    log("expand and rename solution | is solution but not zipfile or tarfile")
                else:
                    # try extract solution archive file 
                    problem_solutions = extract_archives([path])
                    env.cwd = get_directory_content(env)
                    env.cwd.proj.reload_solutions()
                    if problem_solutions:
                        log("extract | problem archives: "+str(problem_solutions))
                    else:
                        # try rename sut
                        solution_name = os.path.basename(remove_archive_suffix(path))
                        solution = None
                        if solution_name in env.cwd.proj.solutions:
                            solution = env.cwd.proj.solutions[solution_name]
                        if solution is not None:
                            ok, renamed, fail = rename_solutions(env.cwd.proj, solution=solution)
    # ======================= CLEAN =======================
    elif fce == TEST_CLEAN_ALL:
        if env.cwd.proj is not None:
            solution_list = []
            for dir_name in env.cwd.dirs:
                solution_name = os.path.basename(dir_name)
                if solution_name in env.cwd.proj.solutions:
                    solution_list.append(env.cwd.proj.solutions[solution_name])

            # for key, solution in env.cwd.proj.solutions.items():
            for solution in solution_list:
                clean_test(solution)
            env.cwd = get_directory_content(env)
    elif fce == TEST_CLEAN: # on solution dir
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            clean_test(solution)
            env.cwd = get_directory_content(env)
    # ======================= RUN TESTSUITE =======================
    elif fce == TEST_ALL_STUDENTS: # ALL STUDENTS
        if env.cwd.proj is not None:
            solution_list = []
            for dir_name in env.cwd.dirs:
                solution_name = os.path.basename(dir_name)
                if solution_name in env.cwd.proj.solutions:
                    solution_list.append(env.cwd.proj.solutions[solution_name])

            # for key, solution in env.cwd.proj.solutions.items():
            for solution in solution_list:
                env = run_testsuite(env, solution, show_results=False)
                if env.is_exit_mode():
                    return env, True
            env.cwd = get_directory_content(env)
    elif fce == TEST_STUDENT: # on solution dir
        """ run testsuite on student solution directory """
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            env = run_testsuite(env, solution) # run testsuite in docker
            if env.is_exit_mode():
                return env, True
            env.cwd = get_directory_content(env)
    # ======================= RUN TEST (TODO)=======================
    elif fce == RUN_TEST: # on solution dir
        """ select one or more tests and run this tests on student solution directory """
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            """ show menu with tests for selection """
            title = "Select one or more tests and press 'enter' to run them sequentially..."
            test_names = get_tests_names(env)
            test_names.sort()
            env, option_list = brows_menu(stdscr, env, test_names, keys=True, select_multiple=True, title=title)
            if env.is_exit_mode():
                return env, True
            screen, win = env.get_screen_for_current_mode()
            curses.curs_set(0)

            if option_list is not None:
                tests = []
                for option_idx in option_list:
                    if len(test_names) > option_idx:
                        test_name = test_names[option_idx]
                        tests.append(test_name)
                # run selected tests
                env = run_tests(env, solution, tests)
                env.cwd = get_directory_content(env)
                return env, True
    # =================== GENERATE REPORT ===================
    elif fce == GEN_CODE_REVIEW: # on solution dir
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            generate_code_review(env, solution)
            env.cwd = get_directory_content(env)
    elif fce == GEN_TOTAL_REPORT: # on solution dir
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            # check for report dir and report template
            report_dir = os.path.join(env.cwd.proj.path, REPORT_DIR)
            create_report_dir(report_dir)
            generate_report_from_template(env, solution)
    # ======================= ADD TEST NOTES TO REPORT =======================
    elif fce == ADD_TEST_NOTE_TO_ALL:
        # get list of solutions to which will be added note
        solution_list = []
        for dir_name in env.cwd.dirs:
            solution_name = os.path.basename(dir_name)
            if solution_name in env.cwd.proj.solutions:
                solution_list.append(env.cwd.proj.solutions[solution_name])
        if solution_list:
            # get text from user input
            title = "Enter a test note (related to current version of testsuite):"
            env, note_text = get_user_input(stdscr, env, title=title)
            if env.is_exit_mode():
                return env, True
            screen, win = env.get_screen_for_current_mode()
            curses.curs_set(0)
            if note_text is not None:
                note_text = ''.join(note_text).strip()
                add_test_note_to_solutions(env, solution_list, note_text)
    elif fce == ADD_TEST_NOTE: # on solution
        # add note to auto report from tests
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            # get text from user input
            title = "Enter a test note (related to current version of testsuite):"
            env, note_text = get_user_input(stdscr, env, title=title)
            if env.is_exit_mode():
                return env, True
            screen, win = env.get_screen_for_current_mode()
            curses.curs_set(0)
            if note_text is not None:
                note_text = ''.join(note_text).strip()
                add_test_note_to_solutions(env, [solution], note_text)
    # ======================= ADD USER NOTES TO REPORT =======================
    elif fce == ADD_USER_NOTE_TO_ALL:
        # get list of solutions to which will be added note
        solution_list = []
        for dir_name in env.cwd.dirs:
            solution_name = os.path.basename(dir_name)
            if solution_name in env.cwd.proj.solutions:
                solution_list.append(env.cwd.proj.solutions[solution_name])
        if solution_list:
            # get text from user input
            title = "Enter a note for project solution:"
            env, note_text = get_user_input(stdscr, env, title=title)
            if env.is_exit_mode():
                return env, True
            screen, win = env.get_screen_for_current_mode()
            curses.curs_set(0)
            if note_text is not None:
                note_text = ''.join(note_text).strip()
                for solution in solution_list:
                    # add user note
                    solution.add_user_note(note_text)
                    save_user_notes_for_solution(solution)
    elif fce == ADD_USER_NOTE: # on solution
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            # get text from user input
            title = "Enter a note for project solution:"
            env, note_text = get_user_input(stdscr, env, title=title)
            if env.is_exit_mode():
                return env, True
            screen, win = env.get_screen_for_current_mode()
            curses.curs_set(0)
            if note_text is not None:
                note_text = ''.join(note_text).strip()
                # add user note
                solution.add_user_note(note_text)
                save_user_notes_for_solution(solution)
    # ======================= ADD TAG =======================
    elif fce == ADD_TAG_TO_ALL:
        # get list of solutions to which will be added note
        solution_list = []
        for dir_name in env.cwd.dirs:
            solution_name = os.path.basename(dir_name)
            if solution_name in env.cwd.proj.solutions:
                solution_list.append(env.cwd.proj.solutions[solution_name])
        if solution_list:
            # get tag from user input
            title = "Enter new tag in format: tag_name param1 param2 ..."
            env, text = get_user_input(stdscr, env, title=title)
            if env.is_exit_mode():
                return env, True
            screen, win = env.get_screen_for_current_mode()
            curses.curs_set(0)
            if text is not None:
                tag_parts = shlex.split(''.join(text))
                if len(tag_parts)>0:
                    tag_name, *args = tag_parts
                    # add tag to listed solutions
                    for solution in solution_list:
                        solution.tags.set_tag(tag_name, args)
                        save_tags_to_file(solution.tags)
    # ======================= SHOW INFO =======================
    elif fce == SHOW_OR_HIDE_PROJ_INFO:
        env.show_solution_info = not env.show_solution_info
    elif fce == SHOW_CODE_REVIEW: # on solution dir
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            # open generated code review
            code_review_file = os.path.join(solution.path, REPORT_DIR, CODE_REVIEW_FILE)
            if os.path.exists(code_review_file):
                env.set_file_to_open(code_review_file)
                env.set_view_mode()
                return env, True
            else:
                log(f"cant find code review file | '{code_review_file}' doesnt exists")
    elif fce == SHOW_TEST_NOTES: # on solution dir
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            # open file with test notes
            test_notes_file = os.path.join(solution.path, REPORT_DIR, TEST_NOTES_FILE)
            if os.path.exists(test_notes_file):
                env.set_file_to_open(test_notes_file)
                env.set_view_mode()
                return env, True
            else:
                log(f"cant find file with test notes | '{test_notes_file}' doesnt exists")
    elif fce == SHOW_USER_NOTES: # on solution dir
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            # open file with user notes
            user_notes_file = os.path.join(solution.path, REPORT_DIR, USER_NOTES_FILE)
            if os.path.exists(user_notes_file):
                env.set_file_to_open(user_notes_file)
                env.set_view_mode()
                return env, True
            else:
                log(f"cant find file with user notes | '{user_notes_file}' doesnt exists")
    elif fce == SHOW_TOTAL_REPORT: # on solution dir
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            # open generated report
            report_file = os.path.join(solution.path, REPORT_DIR, TOTAL_REPORT_FILE)
            if os.path.exists(report_file):
                env.set_file_to_open(report_file)
                env.set_view_mode()
                return env, True
            else:
                log(f"cant find report file | '{report_file}' doesnt exists")
    elif fce == SHOW_TEST_RESULTS: # on solution dir
        idx = win.cursor.row
        solution = try_get_solution_from_selected_item(env, idx)
        if solution is not None:
            # go to solution/tests/ dir
            test_dir = os.path.join(solution.path, TESTS_DIR)
            os.chdir(test_dir)
            env.cwd = get_directory_content(env)
            win.reset(0,0)
    # ======================= SHOW STATS =======================
    elif fce == SHOW_STATS:
        generate_scoring_stats(env)
    elif fce == SHOW_HISTOGRAM:
        pass
    # =================== ADD TEST ===================
    elif fce == ADD_TEST:
        env.update_win_for_current_mode(win)
        rewrite_all_wins(env)

        # get test name from user input
        title = "Enter a name/identifier for new test:"
        env, test_name = get_user_input(stdscr, env, title=title)
        if env.is_exit_mode():
            return env, True
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
        if test_name is not None:
            test_name = ''.join(test_name).strip()
            test_name = re.sub("\s+","_",test_name)

            # create dir for new test (and go to new test dir)
            new_test_dir = create_new_test(env.cwd.path, test_name)
            if new_test_dir is not None:
                os.chdir(new_test_dir)
                env.cwd = get_directory_content(env)
                win.reset(0,0)

                # open shell script "dotest.sh" to implement the test
                env.set_file_to_open(os.path.join(new_test_dir, TEST_FILE), is_test_file=True)
                env.switch_to_next_mode()
                return env, True
    # =================== EDIT TESTSUITE ===================
    elif fce == EDIT_TESTSUITE:
        if env.cwd.proj is not None:
            tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
            if os.path.exists(tests_dir):
                # create testsuite file if not exists
                testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)
                create_testsuite(testsuite_file)

                # open "testsuite.sh" to implement testing strategy
                env.set_file_to_open(testsuite_file)
                env.switch_to_next_mode()
                return env, True
            else:
                log(f"cant create testsuite file in tests dir | '{tests_dir}' doesnt exists ")
    # =================== CHANGE SCORING ===================
    elif fce == CHANGE_SCORING:
        if env.cwd.proj is not None:
            scoring_file = os.path.join(env.cwd.proj.path, TESTS_DIR, SCORING_FILE)
            if os.path.exists(scoring_file):
                env.set_file_to_open(scoring_file)
                env.switch_to_next_mode()
                return env, True
            else:
                log(f"cant find scoring file | '{scoring_file}' doesnt exists")
    # =================== CHANGE SUM ===================
    elif fce == CHANGE_SUM:
        if env.cwd.proj is not None:
            sum_file = os.path.join(env.cwd.proj.path, TESTS_DIR, SUM_FILE)
            if os.path.exists(sum_file):
                env.set_file_to_open(sum_file)
                env.switch_to_next_mode()
                return env, True
            else:
                log(f"cant find sum file | '{sum_file}' doesnt exists")
    # =================== EDIT TEST ===================
    elif fce == EDIT_TEST:
        if env.cwd.proj is not None:
            """ show menu with tests for selection """
            title = "Select test to open for edit..."
            test_names = get_tests_names(env)
            test_names.sort()
            env, option_idx = brows_menu(stdscr, env, test_names, keys=True, title=title)
            if env.is_exit_mode():
                return env, True
            screen, win = env.get_screen_for_current_mode()
            curses.curs_set(0)

            if option_idx is not None:
                if len(test_names) > option_idx:
                    test_name = test_names[option_idx]
                    test_dir = os.path.join(env.cwd.proj.path, TESTS_DIR, test_name)
                    # go to test dir
                    os.chdir(test_dir)
                    env.cwd = get_directory_content(env)
                    win.reset(0,0)

                    # open 'dotest.sh' to edit
                    test_file = os.path.join(test_dir, TEST_FILE)
                    if os.path.exists(test_file):
                        env.set_file_to_open(test_file)
                        env.switch_to_next_mode()
                        return env, True
                    else:
                        log(f"edit test | cant find '{test_file}' file for test")
    # =================== REMOVE TEST ===================
    elif fce == REMOVE_TEST:
        idx = win.cursor.row
        dirs_and_files = env.cwd.get_all_items()
        if env.cwd.proj is not None and len(dirs_and_files)>idx:
            selected_item = os.path.join(env.cwd.path, dirs_and_files[idx]) # selected item
            test_dir = None
            if is_testcase_dir(env.cwd.path):
                test_dir = env.cwd.path
            elif is_testcase_dir(selected_item):
                test_dir = selected_item

            # copy test dir to history
            if test_dir is not None:
                test_name = os.path.basename(test_dir)
                succ = history_test_removed(env.cwd.proj.path, test_name)
                if succ:
                    # remove test dir
                    shutil.rmtree(test_dir)
                    env.cwd = get_directory_content(env)

                    # check if test dir is in sum equation -> warning (test in sum equation)
                    sum_file = os.path.join(env.cwd.proj.path, TESTS_DIR, SUM_FILE)
                    if os.path.exists(sum_file):
                        with open(sum_file, 'r') as f:
                            if test_name in f.read():
                                log(f"remove test | warning - test '{test_name}' may be included in total sum equation (check '{sum_file}' file)")

                    # check if test dir is in testsuite.sh -> warning (test in testsuite.sh)
                    testsuite_file = os.path.join(env.cwd.proj.path, TESTS_DIR, TESTSUITE_FILE)
                    if os.path.exists(testsuite_file):
                        with open(testsuite_file, 'r') as f:
                            if test_name in f.read():
                                log(f"remove test | warning - test '{test_name}' may be included in testsuite (check '{testsuite_file}' file)")

                    # check if solution has test tag -> warning (test results in solution: {solution})
                    # TODO: warning - this may take some time... (depending on how many solution dirs are in this project) do you want to continue?

    # =================== CREATE DOCKER IMAGE ===================
    elif fce == CREATE_DOCKER_IMAGE:
        pass

    env.update_win_for_current_mode(win)
    return env, False