
import curses
import curses.ascii
import os


from views.filtering import filter_management
from views.help import show_help

from modules.directory import Directory

from utils.loading import load_buffer_and_tags
from utils.screens import *
from utils.printing import *
from utils.logger import *



def get_directory_content():
    path = os.getcwd() # current working directory
    files, dirs = [], []
    for dir_path, dir_names, file_names in os.walk(path):
        files.extend(file_names)
        dirs.extend(dir_names)
        break
    dirs.sort()
    files.sort()
    return Directory(path, dirs, files)



def directory_browsing(stdscr, conf):
    curses.curs_set(0)
    screen, win = conf.get_screen_for_current_mode()


    if conf.filter_not_empty():
        cwd = Directory(conf.filter.project, files=conf.filter.files)
    else:
        cwd = get_directory_content()
    conf.cwd = cwd


    while True:
        """ try to load buffer and tag for current file in directory structure """
        if conf.quick_view:
            idx = win.cursor.row
            if idx >= len(cwd.dirs) and idx < len(cwd): # selected item is file
                dirs_and_files = cwd.get_all_items()
                conf.set_file_to_open(os.path.join(cwd.path, dirs_and_files[idx]))
                new_conf, buffer, succ = load_buffer_and_tags(conf) # try to load file
                if not succ: # couldnt load buffer and/or fags for current file
                    conf.set_file_to_open(None)
                    conf.set_brows_mode() # instead of exit mode
                else:
                    """ calculate line numbers """
                    if conf.line_numbers:
                        new_conf.enable_line_numbers(buffer)
                        new_conf.right_up_win.set_line_num_shift(len(new_conf.line_numbers)+1)
                    conf = new_conf
            else:
                conf.set_file_to_open(None)

        """ print all screens """
        conf.update_browsing_data(win, cwd)
        rewrite_all_wins(conf)

        key = stdscr.getch()

        try:
            # ======================= EXIT =======================
            if key == curses.KEY_F10: # if key F10 doesnt work, use alternative ALT+0
                conf.update_browsing_data(win, cwd) # save browsing state before exit browsing
                conf.set_exit_mode()
                return conf
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                conf.update_browsing_data(win, cwd)
                conf.set_view_mode()
                return conf
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(cwd, use_restrictions=False)
            elif key == curses.KEY_DOWN:
                win.down(cwd, filter_on=conf.path_filter_on(), use_restrictions=False)
            elif key == curses.KEY_RIGHT:
                idx = win.cursor.row
                if not conf.filter_not_empty() and idx < len(cwd.dirs):
                    """ go to subdirectory """
                    os.chdir(os.path.join(cwd.path, cwd.dirs[idx]))
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0) # set cursor on first position (first item)
            elif key == curses.KEY_LEFT:
                current_dir = os.path.basename(cwd.path) # get directory name
                if not conf.filter_not_empty() and current_dir: # if its not root
                    """ go to parent directory """
                    os.chdir('..')
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0)
                    """ set cursor position to prev directory """
                    dir_position = cwd.dirs.index(current_dir) # find position of prev directory
                    if dir_position:
                        for i in range(0, dir_position):
                            win.down(cwd, filter_on=conf.path_filter_on(), use_restrictions=False)
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen, win = conf.left_screen, conf.left_win
            # ======================= F KEYS =======================
            elif key == curses.KEY_F1: # help
                conf.update_browsing_data(win, cwd)
                conf = show_help(stdscr, conf)
                screen, win = conf.left_screen, conf.left_win
                curses.curs_set(0)
            elif key == curses.KEY_F4:
                idx = win.cursor.row
                if idx >= len(cwd.dirs) or conf.filter: # cant open direcotry
                    conf.update_browsing_data(win, cwd)
                    dirs_and_files = cwd.get_all_items()
                    conf.enable_file_edit()
                    conf.set_file_to_open(os.path.join(cwd.path, dirs_and_files[idx]))
                    conf.set_view_mode()
                    return conf
            elif key == curses.KEY_F3:
                conf.update_browsing_data(win, cwd)
                conf.quick_view = not conf.quick_view
            elif key == curses.KEY_F9: # set filter
                conf = filter_management(stdscr, screen, win, conf)
                if conf.is_exit_mode():
                    return conf
                screen, win = conf.left_screen, conf.left_win
                # actualize current working directory according to filter
                if conf.filter_not_empty():
                    cwd = Directory(conf.filter.project, files=conf.filter.files)
                else:
                    conf.cwd = get_directory_content()
                    cwd = conf.cwd
                win.reset_shifts()
                win.set_cursor(0,0)
        except Exception as err:
            log("browsing with quick view | "+str(err))
            conf.set_exit_mode()
            return conf