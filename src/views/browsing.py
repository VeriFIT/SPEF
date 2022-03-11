
import curses
import curses.ascii
import os
import traceback

from controls.control import *

from views.filtering import filter_management
from views.help import show_help
from views.menu import brows_menu

from modules.directory import Directory, Project

from utils.loading import *
from utils.screens import *
from utils.printing import *
from utils.logger import *


def get_directory_content(env):
    if env.filter_not_empty():
        cwd = Directory(env.filter.project, files=env.filter.files)
        cwd.proj_conf_path = env.filter.project
        return cwd

    path = os.getcwd() # current working directory path
    files, dirs = [], []
    for dir_path, dir_names, file_names in os.walk(path):
        if env.show_cached_files:
            files.extend(file_names)
        else:
            for file_name in file_names:
                if not file_name.endswith((REPORT_SUFFIX,TAGS_SUFFIX)):
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
                env.set_file_to_open(os.path.join(env.cwd.path, dirs_and_files[idx]))
                env, buffer, succ = load_buffer_and_tags(env) # try to load file
                if not succ: # couldnt load buffer and/or fags for current file
                    env.set_file_to_open(None)
                    env.set_brows_mode() # instead of exit mode
                else:
                    """ set line numbers """
                    if env.line_numbers or env.start_with_line_numbers:
                        env.start_with_line_numbers = False
                        env.enable_line_numbers(buffer)
                        env = resize_all(stdscr, env, True)
            # if its project directory, show project info and test results
            else:
                if env.cwd.is_project_subdirectory(): # current working directory is a project subdirectory (ex: "proj1/")
                    # env.cwd.proj
                    selected_dir = dirs_and_files[idx]
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
    # ======================= FOCUS =======================
    elif fce == CHANGE_FOCUS:
        env.switch_to_next_mode()
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
        menu_functions = {
            'create new project': ADD_PROJECT,
            'create new test': ADD_PROJECT, # sprava testov
            'remove test': ADD_PROJECT,
            'edit test': ADD_PROJECT,
            'run test': ADD_PROJECT,
            'create new testset': ADD_PROJECT,
            'run testset': ADD_PROJECT,
            'define test failure': ADD_PROJECT,
            'create new directory': ADD_PROJECT,
            'create new file': ADD_PROJECT, # sprava suborov
            'remove file': ADD_PROJECT,
            'rename file': ADD_PROJECT,
            'copy file': ADD_PROJECT,
            'move file': ADD_PROJECT,
            'edit file': ADD_PROJECT,
            'expand archive here': ADD_PROJECT,
            'expand archive to ...': ADD_PROJECT,
            'show project info': ADD_PROJECT, # zobrazovanie info
            'hide project info': ADD_PROJECT,
            'show statistics': ADD_PROJECT,
            'show histogram': ADD_PROJECT
        }
        title = "Select function from menu: "
        color = curses.color_pair(COL_TITLE)
        menu_options = [key for key in menu_functions]
        env, option_idx = brows_menu(stdscr, env, menu_options, color=color, title=title)
        if env.is_exit_mode():
            return env, True
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
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
    # ======================= OPEN FILE =======================
    elif fce == OPEN_FILE:
        idx = win.cursor.row
        if idx >= len(env.cwd.dirs) or env.filter: # cant open direcotry
            dirs_and_files = env.cwd.get_all_items()
            env.enable_file_edit()
            env.set_file_to_open(os.path.join(env.cwd.path, dirs_and_files[idx]))
            env.switch_to_next_mode()
            return env, True
    # ======================= DELETE FILE =======================
    elif fce == DELETE_FILE:
        idx = win.cursor.row
        dirs_and_files = env.cwd.get_all_items()
        file_to_delete = os.path.join(env.cwd.path, dirs_and_files[idx])
        if os.path.exists(file_to_delete):
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


    if fce == OPEN_FILE:
        idx = win.cursor.row
        if idx >= len(env.cwd.dirs) or env.filter: # cant open direcotry
            dirs_and_files = env.cwd.get_all_items()
            env.enable_file_edit()
            env.set_file_to_open(os.path.join(env.cwd.path, dirs_and_files[idx]))
            env.switch_to_next_mode()
            return env, True
    # ======================= ADD PROJECT =======================
    elif fce == ADD_PROJECT:
        if env.cwd.is_project_subdirectory():
            return env, False
        # create project object
        proj = Project(env.cwd.path)
        proj.set_default_values()

        # create project config file
        proj_data = proj.to_dict()
        save_proj_to_conf_file(proj.path, proj_data)

        # actualize current working directory
        env.cwd = get_directory_content(env)
    # ======================== ADD TEST ========================
    # elif fce == ADD_TEST:
    #     pass
    # ====================== RUN ALL TESTS ======================
    # elif fce == RUN_ALL_TESTS:
    #     pass
    # ======================= RUN TEST SET =======================
    # elif fce == RUN_TEST_SET:
    #     pass
    # =================== GENERATE AUTO REPORT ===================
    # elif fce == GEN_AUTO_REPORT:
    #     pass


    env.update_win_for_current_mode(win)
    return env, False