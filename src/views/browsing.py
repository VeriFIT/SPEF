
import curses
import curses.ascii
import os
import shutil
import traceback
import tarfile
import zipfile

from controls.control import *
from controls.functions import brows_menu_functions

from views.filtering import filter_management
from views.help import show_help
from views.menu import brows_menu
from views.input import get_user_input

from modules.directory import Directory, Project
from modules.bash import Bash_action

from utils.loading import *
from utils.screens import *
from utils.printing import *
from utils.logger import *
from utils.reporting import *
from utils.match import *
from utils.file import *
from utils.testing import *



def get_directory_content(env):
    if env.filter_not_empty():
        cwd = Directory(env.filter.root, files=env.filter.files)
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
            if idx >= len(env.cwd.dirs):
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

                if env.cwd.proj is not None: # current working directory is a project subdirectory (ex: "proj1/")
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
        env = show_help(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
    # ======================= OPEN MENU =======================
    elif fce == OPEN_MENU:
        idx = win.cursor.row
        dirs_and_files = env.cwd.get_all_items()
        selected_item = os.path.join(env.cwd.path, dirs_and_files[idx]) # selected item
        # show menu with functions
        in_proj_dir = is_in_project_dir(selected_item)
        in_solution_dir = is_in_solution_dir(env.cwd.proj.solution_id, selected_item) if env.cwd.proj is not None else False
        is_test_dir = is_testcase_dir(env.cwd.path) or is_testcase_dir(selected_item)
        menu_functions = get_menu_functions(in_proj_dir, in_solution_dir, is_test_dir)
        # menu_functions = brows_menu_functions()

        title = "Select function from menu: "
        color = curses.color_pair(COL_TITLE)
        menu_options = [key for key in menu_functions]
        env, option_idx = brows_menu(stdscr, env, menu_options, color=color, title=title)
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
        if idx >= len(env.cwd.dirs) or env.filter: # cant open directory
            dirs_and_files = env.cwd.get_all_items()
            env.set_file_to_open(os.path.join(env.cwd.path, dirs_and_files[idx]))
            env.switch_to_next_mode()
            return env, True
    # ======================= DELETE FILE =======================
    elif fce == DELETE_FILE:
        idx = win.cursor.row
        dirs_and_files = env.cwd.get_all_items()
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



def run_menu_function(stdscr, env, fce, key):
    screen, win = env.get_screen_for_current_mode()

    # ======================= ADD PROJECT =======================
    if fce == ADD_PROJECT:
        if env.cwd.proj is not None:
            return env, False
        # create project object
        proj = Project(env.cwd.path)
        proj.set_default_values()
        # create project config file
        proj_data = proj.to_dict()
        save_proj_to_conf_file(proj.path, proj_data)
        # actualize current working directory
        env.cwd = get_directory_content(env)
    elif fce == EXPAND_HERE:
        pass
    elif fce == EXPAND_TO:
        pass
    elif fce == CREATE_DIR:
        pass
    elif fce == CREATE_FILE:
        pass
    elif fce == REMOVE_FILE:
        pass
    elif fce == RENAME_FILE:
        pass
    elif fce == COPY_FILE:
        pass
    elif fce == MOVE_FILE:
        pass
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
    # ============================ RENAME ===========================
    elif fce == RENAME_ALL_SOLUTIONS: # ALL STUDENTS
        if env.cwd.proj is not None:
            if env.cwd.proj.sut_required == "":
                log("rename all solutions | there is no defined sut_required in proj config")
            else:
                solutions = get_solution_dirs(env)
                # log(str(solutions))
                required_name = env.cwd.proj.sut_required
                extended_variants = env.cwd.proj.sut_ext_variants
                ok, renamed, fail = rename_solutions(solutions, required_name, extended_variants)
                log("students with correctly named solution file: "+str(ok))
                log("students with wrong named solution file: "+str(renamed))
                log("students with no supported extention of solution file: "+str(fail))
    # ====================== EXPAND AND RENAME ======================
    elif fce == EXPAND_AND_RENAME_SOLUTION: # on solution dir
        if env.cwd.proj is not None:
            idx = win.cursor.row
            dirs_and_files = env.cwd.get_all_items()
            path = os.path.join(env.cwd.path, dirs_and_files[idx]) # selected item
            if is_solution_file(env, env.cwd.proj.solution_id, path):
                if is_archive_file(path):
                    # try extract solution archive file 
                    problem_solutions = extract_archives([path])
                    env.cwd = get_directory_content(env)
                    if problem_solutions:
                        log("extract | problem archives: "+str(problem_solutions))
                    else:
                        # try rename sut
                        dest_dir = remove_archive_suffix(path)
                        required_name = env.cwd.proj.sut_required
                        extended_variants = env.cwd.proj.sut_ext_variants
                        ok, renamed, fail = rename_solutions([dest_dir], required_name, extended_variants)
                else:
                    log("expand and rename solution | is solution but not zipfile or tarfile")
    # ======================= RUN TEST SET =======================
    elif fce == TEST_ALL_STUDENTS: # ALL STUDENTS
        pass
    elif fce == TEST_STUDENT: # on solution dir
        """ run testsuite on student solution directory """
        if env.cwd.proj is not None:
            idx = win.cursor.row
            dirs_and_files = env.cwd.get_all_items()
            selected_item = os.path.join(env.cwd.path, dirs_and_files[idx]) # selected item
            solution = None
            if is_root_solution_dir(env.cwd.proj.solution_id, env.cwd.path):
                solution = env.cwd.path
            elif is_root_solution_dir(env.cwd.proj.solution_id, selected_item):
                solution = selected_item

            if solution is not None:
                env = run_testsuite(stdscr, env, solution)
                return env, True

                # tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
                # t_script = os.path.join(tests_dir, 'src', 't')
                # command = f"cd {solution}\n{t_script}\n"

                # env.bash_action = Bash_action()
                # env.bash_action.dont_jump_to_cwd()
                # env.bash_action.add_command(command)
                # env.bash_active = True
                # return env, True
    elif fce == RUN_TEST: # on solution dir
        """ select one or more tests and run this tests on student solution directory """
        if env.cwd.proj is not None:
            idx = win.cursor.row
            dirs_and_files = env.cwd.get_all_items()
            selected_item = os.path.join(env.cwd.path, dirs_and_files[idx]) # selected item
            solution = None
            if is_root_solution_dir(env.cwd.proj.solution_id, env.cwd.path):
                solution = env.cwd.path
            elif is_root_solution_dir(env.cwd.proj.solution_id, selected_item):
                solution = selected_item

            """ show menu with tests for selection """
            # title = "Press 'enter' to select test, press 'esc' to run selected tests..."
            # selected_tests = []
            # run_selection = True
            # while run_selection:
            #     # show menu
            #     key = stdscr.getch()
            #     if key == '\n':
            #         run_selection = False
            #     elif key == 's':

            #     test_names = get_valid_tests_names(env)
            #     title = "Select from typical notes: "
            #     color = curses.color_pair(COL_TITLE)
            #     env, option_idx = brows_menu(stdscr, env, test_names, color=color, title=title)


            #     options = {}
            #     if len(test_names) > 0:
            #         for idx, name in enumerate(test_names):
            #             if idx+1 > 35:
            #                 break
            #             key = idx+1 if idx < 9 else chr(idx+1+55) # 1-9 or A-Z (chr(10+55)='A')
            #             options[str(idx+1)] = name

            #     options = env.get_typical_notes_dict()
            #     char_key = chr(key)
            #     if char_key in options.keys():
            #         str_text = options[char_key]
            #         note_row, note_col = win.cursor.row, win.cursor.col - win.begin_x
            #         env.report.add_note(note_row, note_col, str_text)
            #     rewrite_all_wins(env)


            # run_test
    elif fce == TEST_CLEAN: # on solution dir
        pass
    # =================== GENERATE REPORT ===================
    elif fce == GEN_CODE_REVIEW: # on solution dir
        idx = win.cursor.row
        dirs_and_files = env.cwd.get_all_items()
        generate_code_review(env, os.path.join(env.cwd.path, dirs_and_files[idx]))
        env.cwd = get_directory_content(env)
    elif fce == GEN_AUTO_REPORT: # on solution dir
        pass
    # ======================= ADD NOTES TO REPORT =======================
    elif fce == ADD_AUTO_NOTE:
        pass
    elif fce == ADD_USER_NOTE:
        pass
    # ======================= SHOW INFO =======================
    elif fce == SHOW_OR_HIDE_PROJ_INFO:
        env.show_solution_info = not env.show_solution_info
    elif fce == SHOW_CODE_REVIEW: # on solution dir
        pass
    elif fce == SHOW_AUTO_REPORT: # on solution dir
        pass
    elif fce == SHOW_TOTAL_REPORT: # on solution dir
        pass
    elif fce == SHOW_TEST_RESULTS: # on solution dir
        pass
    # ======================= SHOW STATS =======================
    elif fce == SHOW_STATS:
        pass
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
                env.set_file_to_open(os.path.join(new_test_dir, TEST_FILE))
                env.switch_to_next_mode()
                return env, True
    # =================== EDIT TESTSUITE ===================
    elif fce == EDIT_TESTSUITE:
        if env.cwd.proj is not None:
            tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
            if os.path.exists(tests_dir):
                # create testsuite file if not exists
                testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)
                create_test_suite(testsuite_file)

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
    # =================== DEFINE TEST FAILURE ===================
    elif fce == DEFINE_TEST_FAILURE:
        pass
    # =================== EDIT TEST ===================
    elif fce == EDIT_TEST:
        pass
    # =================== REMOVE TEST ===================
    elif fce == REMOVE_TEST:
        pass

    env.update_win_for_current_mode(win)
    return env, False