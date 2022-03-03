
import curses
import curses.ascii
import os
import traceback

from views.filtering import filter_management
from views.help import show_help

from modules.directory import Directory

from utils.loading import load_buffer_and_tags, REPORT_SUFFIX, TAGS_SUFFIX
from utils.screens import *
from utils.printing import *
from utils.logger import *

from control import *


def get_directory_content(show_cached_files=True):
    path = os.getcwd() # current working directory path
    files, dirs = [], []
    for dir_path, dir_names, file_names in os.walk(path):
        if show_cached_files:
            files.extend(file_names)
        else:
            for file_name in file_names:
                if not file_name.endswith((REPORT_SUFFIX,TAGS_SUFFIX)):
                    files.append(file_name)
        dirs.extend(dir_names)
        break
    dirs.sort()
    files.sort()
    return Directory(path, dirs, files)



def directory_browsing(stdscr, env):
    curses.curs_set(0)
    screen, win = env.get_screen_for_current_mode()


    if env.filter_not_empty():
        cwd = Directory(env.filter.project, files=env.filter.files)
    else:
        cwd = get_directory_content(env.show_cached_files)
    env.cwd = cwd

    while True:
        """ try to load buffer and tag for current file in directory structure """
        if env.quick_view:
            idx = win.cursor.row
            # if its file, show its content and tags
            if idx >= len(env.cwd.dirs) and idx < len(env.cwd):
                dirs_and_files = env.cwd.get_all_items()
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
            env.cwd = get_directory_content(env.show_cached_files)
            win.reset(0,0) # set cursor on first position (first item)
    elif fce == CURSOR_LEFT:
        current_dir = os.path.basename(env.cwd.path) # get directory name
        if not env.filter_not_empty() and current_dir: # if its not root
            """ go to parent directory """
            os.chdir('..')
            env.cwd = get_directory_content(env.show_cached_files)
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
    # ======================= FILTER =======================
    elif fce == FILTER:
        env = filter_management(stdscr, screen, win, env)
        if env.is_exit_mode():
            return env, True
        screen, win = env.get_screen_for_current_mode()
        # actualize current working directory according to filter
        if env.filter_not_empty():
            env.cwd = Directory(env.filter.project, files=env.filter.files)
        else:
            env.cwd = get_directory_content(env.show_cached_files)
        win.reset(0,0)
        curses.curs_set(0)

    env.update_win_for_current_mode(win)
    return env, False
