
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
            if idx >= len(cwd.dirs) and idx < len(cwd): # selected item is file
                dirs_and_files = cwd.get_all_items()
                env.set_file_to_open(os.path.join(cwd.path, dirs_and_files[idx]))
                new_env, buffer, succ = load_buffer_and_tags(env) # try to load file
                if not succ: # couldnt load buffer and/or fags for current file
                    env.set_file_to_open(None)
                    env.set_brows_mode() # instead of exit mode
                else:
                    """ set line numbers """
                    if env.line_numbers:
                        new_env.enable_line_numbers(buffer)
                        new_env = resize_all(stdscr, new_env, True)
                        screen, win = new_env.get_screen_for_current_mode()
                    env = new_env
            else:
                pass
                # env.set_file_to_open(None)

        """ print all screens """
        env.update_browsing_data(win, cwd)
        rewrite_all_wins(env)

        key = stdscr.getch()

        try:
            # ======================= EXIT =======================
            if key == curses.KEY_F10: # if key F10 doesnt work, use alternative ALT+0
                env.update_browsing_data(win, cwd) # save browsing state before exit browsing
                env.set_exit_mode()
                return env
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                env.update_browsing_data(win, cwd)
                env.switch_to_next_mode()
                return env
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(cwd, use_restrictions=False)
            elif key == curses.KEY_DOWN:
                win.down(cwd, filter_on=env.path_filter_on(), use_restrictions=False)
            elif key == curses.KEY_RIGHT:
                idx = win.cursor.row
                if not env.filter_not_empty() and idx < len(cwd.dirs):
                    """ go to subdirectory """
                    os.chdir(os.path.join(cwd.path, cwd.dirs[idx]))
                    cwd = get_directory_content(env.show_cached_files)
                    win.reset(0,0) # set cursor on first position (first item)
            elif key == curses.KEY_LEFT:
                current_dir = os.path.basename(cwd.path) # get directory name
                if not env.filter_not_empty() and current_dir: # if its not root
                    """ go to parent directory """
                    os.chdir('..')
                    cwd = get_directory_content(env.show_cached_files)
                    win.reset(0,0)
                    """ set cursor position to prev directory """
                    dir_position = cwd.dirs.index(current_dir) # find position of prev directory
                    if dir_position:
                        for i in range(0, dir_position):
                            win.down(cwd, filter_on=env.path_filter_on(), use_restrictions=False)
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                env = resize_all(stdscr, env)
                screen, win = env.get_screen_for_current_mode()
            # ======================= F KEYS =======================
            elif key == curses.KEY_F1: # help
                env.update_browsing_data(win, cwd)
                env = show_help(stdscr, env)
                screen, win = env.get_screen_for_current_mode()
                curses.curs_set(0)
            elif key == curses.KEY_F4:
                idx = win.cursor.row
                if idx >= len(cwd.dirs) or env.filter: # cant open direcotry
                    env.update_browsing_data(win, cwd)
                    dirs_and_files = cwd.get_all_items()
                    env.enable_file_edit()
                    env.set_file_to_open(os.path.join(cwd.path, dirs_and_files[idx]))
                    env.switch_to_next_mode()
                    return env
            elif key == curses.KEY_F3:
                env.update_browsing_data(win, cwd)
                env.quick_view = not env.quick_view
            elif key == curses.KEY_F9: # set filter
                env = filter_management(stdscr, screen, win, env)
                if env.is_exit_mode():
                    return env
                screen, win = env.get_screen_for_current_mode()
                # actualize current working directory according to filter
                if env.filter_not_empty():
                    cwd = Directory(env.filter.project, files=env.filter.files)
                else:
                    env.cwd = get_directory_content(env.show_cached_files)
                    cwd = env.cwd
                win.reset(0,0)
        except Exception as err:
            log("browsing with quick view | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env
