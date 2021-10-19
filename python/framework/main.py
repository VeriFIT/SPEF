#!/usr/bin/env python3

import curses
import curses.ascii
import datetime
import json
import os
import sys


from buffer import Buffer
from config import *
from directory import Directory
from window import Window, Cursor

ESC = 27

PROJECT_DIR = "/home/naty/Others/ncurses/python/project"

LOG_FILE = "/home/naty/Others/ncurses/python/framework/log"
TAG_DIR = "/home/naty/Others/ncurses/python/framework/tags"
REPORT_DIR = "/home/naty/Others/ncurses/python/framework/reports"

BORDER = 2
START_Y = 1
START_X = 1


def log(message):
    day = datetime.date.today()
    time = datetime.datetime.now().strftime("%X")
    with open(LOG_FILE, 'a') as f:
        f.write("{} {} | {}\n".format(day,time,message))

def preparation():
    """ clear log file """
    with open(LOG_FILE, 'w+'): pass

    """ create dirs for tags and reports """
    if not os.path.exists(TAG_DIR):
        os.makedirs(TAG_DIR)
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)


# browsing
B_HELP = {"F1":"help", "F2":"menu", "F3":"view/tag",
            "F4":"edit", "F5":"copy", "F6":"rename",
            "F8":"delete", "F9":"filter", "F10":"exit"}

# editing = is_view_mode + edit_allowed
E_HELP = {"F1":"help", "F2":"save", "F3":"view/tag",
            "F4":"note", "F5":"goto", "F8":"reload",
            "F9":"filter", "F10":"exit"}
"""
CTRL + L    hard reload (from original buff)
CTRL + R    show / hide report notes
"""

# viewing = is_view_mode + not edit_allowed
V_HELP = {"F1":"help", "F4":"edit", "F5":"goto",
            "F9":"filter", "F10":"exit"}

# tagging
T_HELP = {"F1":"help", "F4":"edit",
            "F9":"filter", "F10":"exit"}


def print_hint(conf):
    screen = conf.down_screen
    screen.erase()
    screen.border(0)
    size = screen.getmaxyx()

    if conf.is_brows_mode():
        help_dict = B_HELP
    elif conf.is_view_mode():
        help_dict = E_HELP if conf.edit_allowed else V_HELP
    elif conf.is_tag_mode():
        help_dict = T_HELP
    else:
        help_dict = {}

    string = ""
    for key in help_dict:
        hint = " | " + str(key) + ":" + str(help_dict[key])
        if len(string) + len(hint) <= size[1]:
            string += hint
    screen.addstr(1, 1, string[2:])
    screen.refresh()


def resize_all(stdscr, conf):
    """ get cursor positions from old windows """
    l_win_old_row, l_win_old_col = conf.left_win.get_cursor_position()

    try:
        if curses.is_term_resized(curses.LINES,curses.COLS):
            """ screen resize """
            y,x = stdscr.getmaxyx()
            stdscr.clear()
            curses.resizeterm(y,x)
            stdscr.refresh()

            """ create screens with new size """
            screens, windows = create_screens_and_windows(y, x)
            bkgd_col = curses.color_pair(2)
            conf = create_config(screens, windows, bkgd_col, conf)

            """ set new cursor positions to windows """
            l_win_new_row = min(l_win_old_row, conf.left_win.end_y-2)
            l_win_new_col = min(l_win_old_col, conf.left_win.end_x)
            conf.left_win.set_cursor(l_win_new_row, l_win_new_col)

            # TODO: cursor stays in the middle (see window resizing in vim)
            conf.right_win.set_cursor(conf.right_win.begin_y, conf.right_win.begin_x)

            """ rewrite all screens """
            print_hint(conf)
            show_directory_content(conf.left_screen, conf.left_win, conf.cwd, conf.highlight, conf.normal)
            if conf.edit_allowed:
                show_file_content(conf.right_screen, conf.right_win, conf.file_buffer, conf.highlight, conf.normal)
            else:
                show_file_content(conf.right_up_screen, conf.right_up_win, conf.file_buffer, conf.highlight, conf.normal)
                show_tags(conf.right_down_screen, conf.right_down_win, conf.file_tags)
    except Exception as err:
        log("resizing | "+str(err))
    finally:
        return conf


def create_screens_and_windows(height, width):
    half_width = int(width/2)
    d_win_lines = 1

    """ set window size and position """
    d_win_h, d_win_w = d_win_lines + BORDER, width - START_X
    l_win_h, l_win_w = height - d_win_h - START_Y, half_width
    r_win_h, r_win_w = height - d_win_h - START_Y, half_width - START_X

    d_win_y, d_win_x = START_Y + l_win_h, START_X
    l_win_y, l_win_x = START_Y, START_X
    r_win_y, r_win_x = START_Y, START_X + l_win_w

    left_screen = curses.newwin(l_win_h, l_win_w, l_win_y, l_win_x) # browsing
    right_screen = curses.newwin(r_win_h, r_win_w, r_win_y, r_win_x) # editing
    down_screen = curses.newwin(d_win_h, d_win_w, d_win_y, d_win_x) # hint

    right_up_h = int(r_win_h / 2) + int(r_win_h % 2 != 0)
    right_down_h = int(r_win_h / 2)

    right_up_screen = curses.newwin(right_up_h, r_win_w, r_win_y, r_win_x)
    right_down_screen = curses.newwin(right_down_h, r_win_w, r_win_y + right_up_h, r_win_x)

    right_win = Window(r_win_h, r_win_w, r_win_y+1, r_win_x+1) # +1 stands for bordes at first line and col
    left_win = Window(l_win_h, l_win_w, 0, 0)

    right_up_win = Window(right_up_h, r_win_w, r_win_y+1, r_win_x+1)
    right_down_win = Window(right_down_h, r_win_w, r_win_y+right_up_h+1, r_win_x+1)

    screens = {"LS":left_screen, "RS":right_screen, "DS":down_screen,
                "RUS":right_up_screen, "RDS":right_down_screen}
    windows = {"LW":left_win, "RW":right_win, 
                "RUW":right_up_win, "RDW":right_down_win}

    return screens, windows


def create_config(screens, windows, bkgd_col=None, config=None):
    if config:
        config.left_screen = screens["LS"]
        config.right_screen = screens["RS"]
        config.down_screen = screens["DS"]
    else:
        config = Config(screens["LS"], screens["RS"], screens["DS"])

    config.right_up_screen = screens["RUS"]
    config.right_down_screen = screens["RDS"]

    config.right_win = windows["RW"]
    config.left_win = windows["LW"]
    config.right_up_win = windows["RUW"]
    config.right_down_win = windows["RDW"]

    if bkgd_col:
        config.left_screen.bkgd(' ', bkgd_col)
        config.right_screen.bkgd(' ', bkgd_col)
        config.down_screen.bkgd(' ', bkgd_col)
        config.right_up_screen.bkgd(' ', bkgd_col)
        config.right_down_screen.bkgd(' ', bkgd_col)

    return config


def show_main_screens(stdscr, config):
    stdscr.erase()
    config.left_screen.border(0)
    config.right_screen.border(0)
    config.down_screen.border(0)

    stdscr.refresh()
    config.left_screen.refresh()
    config.right_screen.refresh()
    config.down_screen.refresh()


""" ======================= START MAIN ========================= """
def main(stdscr):
    log("START")
    stdscr.clear()
    curses.set_escdelay(1)

    """ set coloring """
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

    highlight = curses.color_pair(1)
    normal = curses.A_NORMAL
    bkgd_col = curses.color_pair(2)

    """ create screen for browsing, editing and showing hint """
    screens, windows = create_screens_and_windows(curses.LINES, curses.COLS)

    """ create config """
    config = create_config(screens, windows, bkgd_col=bkgd_col)
    config.left_win.set_cursor(0,0)
    config.set_coloring(highlight, normal)
    stdscr.bkgd(' ', bkgd_col)

    """ show all main screens """
    show_main_screens(stdscr, config)

    """ get current files and dirs """
    config.cwd = get_directory_content()

    while True:
        print_hint(config)
        if config.is_exit_mode():
            break
        elif config.is_brows_mode():
            config = directory_browsing(stdscr, config)
        elif config.is_view_mode():
            config = file_viewing(stdscr, config)
        elif config.is_tag_mode():
            config = tag_management(stdscr, config)

    log("END")
""" ======================= END MAIN ========================= """


""" **************************** START BROWSING **************************** """
def directory_browsing(stdscr, conf):
    curses.curs_set(0) # set cursor as invisible

    screen = conf.left_screen
    win = conf.left_win
    cwd = conf.cwd

    while True:
        """ print current directory structure """
        show_directory_content(screen, win, cwd, conf.highlight, conf.normal)

        key = stdscr.getch()
        try:
            # ======================= EXIT =======================
            if key in (curses.ascii.ESC, curses.KEY_F10): # if key F10 doesnt work, use alternative ALT+0
                conf = config_browsing(conf, win, cwd) # save browsing state before exit browsing
                if file_changes_are_saved(stdscr, conf):
                    conf.set_exit_mode()
                    return conf
                else:
                    show_directory_content(screen, win, cwd, conf.highlight, conf.normal)
                    continue
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB: # ord('\t')
                conf = config_browsing(conf, win, cwd)
                conf.set_view_mode()
                return conf
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(cwd, use_restrictions=False)
            elif key == curses.KEY_DOWN:
                win.down(cwd, use_restrictions=False)
            elif key == curses.KEY_RIGHT:
                if win.cursor.row < len(cwd.dirs):
                    """ go to subdirectory """
                    os.chdir(os.getcwd()+'/'+cwd.dirs[win.cursor.row])
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0) # set cursor on first position (first item)
            elif key == curses.KEY_LEFT:
                """ go to parent directory """
                current_dir = os.path.basename(os.getcwd()) # get directory name
                if current_dir: # if its not root
                    os.chdir('..')
                    cwd = get_directory_content()
                    win.reset_shifts()
                    win.set_cursor(0,0)
                    """ set cursor position to prev directory """
                    dir_position = cwd.dirs.index(current_dir) # find position of prev directory
                    if dir_position:
                        for i in range(0, dir_position):
                            win.down(cwd, use_restrictions=False)
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen = conf.left_screen
                win = conf.left_win
            # ======================= F KEYS =======================
            elif key in (curses.KEY_F3, curses.KEY_F4):
                if win.cursor.row >= len(cwd.dirs):
                    conf = config_browsing(conf, win, cwd)
                    dirs_and_files = cwd.get_all_items()
                    conf.file_to_open = os.getcwd()+'/'+dirs_and_files[win.cursor.row]
                    conf.set_view_mode()
                    """ F3: view/tag """
                    if key == curses.KEY_F3:
                        conf.disable_file_edit()
                        conf.right_up_win.reset_window()
                    """ F4: edit """
                    if key == curses.KEY_F4:
                        conf.enable_file_edit()
                        conf.right_win.reset_window()            
                    return conf
        except Exception as err:
            log("browsing | "+str(err))
            conf.set_exit_mode()
            return conf


def get_directory_content():
    path = os.getcwd() # current working directory
    files, dirs = [], []
    for (dir_path,dir_names,file_names) in os.walk(path):
        files.extend(file_names)
        dirs.extend(dir_names)
        break
    dirs.sort()
    files.sort()
    return Directory(path, dirs, files)

def show_directory_content(screen, win, cwd, highlight, normal):
    screen.erase()
    screen.border(0)

    shift = win.row_shift
    if shift > 0:
        dirs, files = cwd.get_shifted_dirs_and_files(shift)
    else:
        dirs = cwd.dirs
        files = cwd.files

    max_cols = win.end_x - win.begin_x
    try:
        if cwd.is_empty():
            screen.addstr(1, 1, "This directory is empty", normal | curses.A_BOLD)
        else:
            i=1
            for dir_name in dirs:
                if i > win.end_y - 1:
                    break
                coloring = (highlight if i+shift == win.cursor.row+1 else normal)
                screen.addstr(i, 1, "/"+str(dir_name[:max_cols-2]), coloring | curses.A_BOLD)
                i+=1
            for file_name in files:
                if i > win.end_y - 1:
                    break
                coloring = highlight if i+shift == win.cursor.row+1 else normal
                screen.addstr(i, 1, str(file_name[:max_cols-1]), coloring)
                i+=1
    except Exception as err:
        log("show directory | "+str(err))
    finally:
        screen.refresh()

""" **************************** END BROWSING **************************** """

def config_browsing(conf, win, cwd):
    conf.left_win = win
    conf.cwd = cwd
    return conf

def config_viewing(conf, win, buffer):
    if conf.edit_allowed:
        conf.right_win = win
    else:
        conf.right_up_win = win
    conf.file_buffer = buffer
    return conf

def config_tagging(conf, win, tags):
    conf.right_down_win = win
    conf.file_tags = tags
    return conf


EXIT_WITHOUT_SAVING_MESSAGE = """WARNING: Exit without saving.\n\
    Press F2 to save and exit.\n\
    Press {} to force exiting without saving.\n\
    Press any other key to continue editing your file."""

RELOAD_FILE_WITHOUT_SAVING = """WARNING: Reload file will discard changes.\n\
    Press F2 to save changes.\n\
    Press {} or Enter to reload file and discard all changes.\n\
    Press any other key to continue editing your file."""

""" check if file changes are saved or user want to save or discard them """
def file_changes_are_saved(stdscr, conf, warning=None, exit_key=None):
    if conf.file_buffer:
        buff = conf.file_buffer
        if (buff.is_saved) or (buff.original_buff == buff.lines):
            return True
        else:
            curses_key, str_key = exit_key if exit_key else (ESC, "ESC")
            message = warning if warning else EXIT_WITHOUT_SAVING_MESSAGE
            """ print warning message """
            screen = conf.right_screen
            screen.erase()
            screen.addstr(1, 1, str(message.format(str_key)), curses.A_BOLD)
            screen.border(0)
            screen.refresh()

            key = stdscr.getch()
            if key == curses_key: # force exit without saving
                return True
            elif key == curses.KEY_F2: # save and exit
                save_buffer(conf.file_to_open, buffer)
                return True
            else:
                return False
    else:
        return True


""" **************************** START VIEWING **************************** """
def file_viewing(stdscr, conf):
    curses.curs_set(1) # set cursor as visible

    screen = conf.right_screen if conf.edit_allowed else conf.right_up_screen
    win = conf.right_win if conf.edit_allowed else conf.right_up_win

    if not conf.file_to_open: # there is no file to open and edit
        conf.set_brows_mode()
        return conf
    file_already_opened = False

    """ try load file content to buffer """
    if conf.file_buffer and conf.file_buffer.file_name == conf.file_to_open:
        file_already_opened = True
        buffer = conf.file_buffer
    else:
        try:
            with open(conf.file_to_open, 'r') as f:
                lines = f.read().splitlines()
            buffer = Buffer(conf.file_to_open, lines)
            conf.file_buffer = buffer
        except Exception as err:
            log("load file content | "+str(err))
            conf.set_exit_mode()
            return conf

    """ try load file tags to config """
    if not conf.edit_allowed and (not conf.file_tags or not file_already_opened):
        # tag file wasnt loaded yet
        try:
            file_name = os.path.basename(conf.file_to_open)
            tag_path = os.path.join(TAG_DIR, str(file_name))
            tag_file = os.path.splitext(tag_path)[0]+".json"
            with open(tag_file, 'r') as f:
                tags = json.load(f)
            conf.file_tags = tags
        except json.decoder.JSONDecodeError:
            conf.file_tags = {}
        except FileNotFoundError:
            conf.file_tags = {}
        except Exception as err:
            log("load file tags | "+str(err))
            conf.set_exit_mode()
            return conf


    while True:
        try:
            """ print current file content and move cursor to correct position """
            show_file_content(screen, win, buffer, conf.highlight, conf.normal)
            if not conf.edit_allowed:
                show_tags(conf.right_down_screen, conf.right_down_win, conf.file_tags)

            new_row, new_col = win.get_cursor_position()
            stdscr.move(new_row, new_col)
        except Exception as err:
            log("viewing | "+str(err))
            conf.set_exit_mode()
            return conf

        key = stdscr.getch()
        try:
            # ======================= EXIT =======================
            if key in (curses.ascii.ESC, curses.KEY_F10): # curses.ascii.ESC
                conf = config_viewing(conf, win, buffer)
                if file_changes_are_saved(stdscr, conf):
                    conf.set_exit_mode()
                    return conf
                else:
                    show_file_content(screen, win, buffer, conf.highlight, conf.normal)
                    continue
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB: # ord('\t')
                conf = config_viewing(conf, win, buffer)
                if conf.edit_allowed:
                    if file_changes_are_saved(stdscr, conf):
                        conf.set_brows_mode()
                    show_file_content(screen, win, buffer, conf.highlight, conf.normal)
                    return conf
                else:
                    conf.set_tag_mode()
                    return conf
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(buffer, use_restrictions=True)
            elif key == curses.KEY_DOWN:
                win.down(buffer, use_restrictions=True)
            elif key == curses.KEY_LEFT:
                win.left(buffer)
            elif key == curses.KEY_RIGHT:
                win.right(buffer)
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen = conf.right_screen if conf.edit_allowed else conf.right_up_screen
                win = conf.right_win if conf.edit_allowed else conf.right_up_win
            else:
                # ***************************** E.D.I.T *****************************
                if conf.edit_allowed:
                    # ======================= EDIT FILE =======================
                    if key == curses.KEY_DC: # \x04 for MacOS which doesnt correctly decode delete key
                        buffer.delete(win)
                    elif key == curses.KEY_BACKSPACE: # \x7f for MacOS
                        if (win.cursor.row, win.cursor.col) > (win.begin_y, win.begin_x):
                            win.left(buffer)
                            buffer.delete(win)
                    elif key == curses.ascii.NL: # ord('\n')
                        buffer.newline(win)
                        win.right(buffer)
                    elif curses.ascii.isprint(key):
                        buffer.insert(win, chr(key))
                        win.right(buffer)
                        # for _ in str_key:
                            # win.right(buffer)
                    # ======================= F KEYS =======================
                    elif key == curses.KEY_F2:
                        """ F2: save file """
                        save_buffer(conf.file_to_open, buffer)
                    elif key == curses.KEY_F3:
                        """ F3: view/tag """
                        conf = config_viewing(conf, win, buffer)
                        if file_changes_are_saved(stdscr, conf):
                            conf.disable_file_edit()
                            return conf
                        else:
                            show_file_content(screen, win, buffer, conf.highlight, conf.normal)
                            continue
                    elif key == curses.KEY_F4:
                        """ F4: note """
                        pass
                    elif key == curses.KEY_F8:
                        """ F8: reload from last save """
                        exit_key = (curses.KEY_F8, "F8")
                        if file_changes_are_saved(stdscr, conf, RELOAD_FILE_WITHOUT_SAVING, exit_key):
                            buffer.lines = buffer.last_save.copy()
                    # ======================= CTRL KEYS =======================
                    elif curses.ascii.iscntrl(key):
                        ctrl_key = curses.ascii.unctrl(key)
                        if ctrl_key == '^L':
                            """ CTRL + L reaload from original buff """
                            buffer.lines = buffer.original_buff.copy()
                        elif ctrl_key == '^R':
                            """ CTRL + R show/hide report notes """
                            conf.note_highlight = not conf.note_highlight
                # ***************************** E.D.I.T *****************************
                # ************************* V.I.E.W / T.A.G *************************
                else:
                    # ======================= F KEYS =======================
                    if key == curses.KEY_F2:
                        pass # TODO F2: ???
                    elif key == curses.KEY_F3:
                        pass # TODO F3: ???
                    elif key == curses.KEY_F4:
                        """ F4: edit """
                        conf.enable_file_edit()
                        pass
                    elif key == curses.KEY_F8:
                        pass # TODO F8: ???
                # ************************* V.I.E.W / T.A.G *************************
        except Exception as err:
            log("viewing | "+str(err))
            conf.set_exit_mode()
            return conf


def save_buffer(file_name, buffer):
    with open(file_name, 'w') as f:
        lines = '\n'.join(buffer.lines)
        f.write(lines)
    buffer.set_save_status(True)
    buffer.last_save = buffer.lines.copy()

def show_file_content(screen, win, buffer, highlight, normal):
    screen.erase()
    screen.border(0)

    max_cols = win.end_x - win.begin_x
    max_rows = win.end_y - win.begin_y

    try:
        if buffer:
            for row, line in enumerate(buffer[win.row_shift : max_rows + win.row_shift - 1]):
                if (row + win.begin_y == win.cursor.row - win.row_shift) and (win.col_shift > 0):
                    line = line[win.col_shift + 1:]
                if len(line) > max_cols:
                    line = line[:max_cols - 1]
                screen.addstr(row+1, 1, line, normal)
    except Exception as err:
        log("show file | "+str(err))
    finally:
        screen.refresh()

""" **************************** END VIEWING **************************** """


""" **************************** START TAGGING **************************** """
def tag_management(stdscr, conf):
    curses.curs_set(1)

    screen = conf.right_down_screen
    win = conf.right_down_win

    """ read tags from file """
    try:
        file_name = os.path.basename(conf.file_to_open)
        tag_path = os.path.join(TAG_DIR, str(file_name))
        tag_file = os.path.splitext(tag_path)[0]+".json"

        if conf.file_tags: # tag file was already loaded
            tags = conf.file_tags
        else:
            with open(tag_file, 'r') as f:
                tags = json.load(f)
            conf.file_tags = tags
    except json.decoder.JSONDecodeError:
        tags = {}
        conf.file_tags = tags
    except FileNotFoundError:
        tags = {}
        conf.file_tags = tags
    except Exception as err:
        log("tagging | "+str(err))
        conf.set_exit_mode()
        return conf

    user_input = []
    pointer = 0

    while True:
        show_tags(screen, win, tags, user_input)

        row, col = win.end_y-2, win.begin_x
        stdscr.move(row, col+pointer)

        key = stdscr.getch()
        try:
            # ======================= EXIT =======================
            if key in (curses.ascii.ESC, curses.KEY_F10): # curses.ascii.ESC
                save_tags(tag_file, tags)
                conf = config_tagging(conf, win, tags)
                conf.set_exit_mode()
                return conf
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                save_tags(tag_file, tags)
                conf = config_tagging(conf, win, tags)
                conf.set_brows_mode()
                return conf
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen = conf.right_down_screen
                win = conf.right_down_win
            # ======================= ARROWS =======================
            elif key == curses.KEY_LEFT:
                if pointer > 0:
                    pointer -= 1
            elif key == curses.KEY_RIGHT:
                if pointer < len(user_input):
                    pointer += 1
            # ======================= INPUT =======================
            elif key == curses.KEY_DC:
                if pointer < len(user_input):
                    del user_input[pointer]
            elif key == curses.KEY_BACKSPACE:
                if pointer > 0:
                    pointer -= 1
                    if pointer < len(user_input):
                        del user_input[pointer]
            elif key == curses.ascii.NL:
                command, tag_name, *args = ''.join(user_input).split()
                if command == "set":
                    tags[tag_name] = [*args]
                elif command == "remove":
                    if tag_name in tags:
                        del tags[tag_name]
                else:
                    # TODO: unknown command, press F1 to see how to use command line utility for tag management
                    log("unknown command")

                save_tags(tag_file, tags)
                user_input = []
                pointer = 0
            elif curses.ascii.isprint(key):
                user_input.insert(pointer, chr(key))
                pointer += 1
            # ======================= F KEYS =======================
            elif key == curses.KEY_F4:
                """ F4: edit """
                conf = config_tagging(conf, win, tags)
                conf.file_to_open = tag_file
                conf.set_view_mode()
                conf.enable_file_edit()
                conf.right_win.reset_window()
                return conf
        except Exception as err:
            log("tagging | "+str(err))
            conf.set_exit_mode()
            return conf

def save_tags(file_name, tags):
    if tags:
        json_string = json.dumps(tags, indent=4, sort_keys=True)
        with open(file_name, 'w+') as f:
            f.write(json_string)


def show_tags(screen, win, tags, command=None):
    screen.erase()
    screen.border(0)

    last_row = win.end_y-win.begin_y-1
    max_cols = win.end_x - win.begin_x
    try:
        if tags:
            for row, name in enumerate(tags):
                if row+2 > last_row:
                    break
                params = tags[name]
                str_params = "(" + ",".join(map(str,params)) + ")"
                line = "#"+str(name)+str_params
                if len(line) > max_cols:
                    line = line[:max_cols - 1]
                screen.addstr(row+1, 1, line)
    except Exception as err:
        log(str(err))
    finally:
        screen.refresh()

    if command:
        command_str = ''.join(command)
        screen.addstr(last_row, 1, command_str)
        screen.refresh()


""" **************************** END TAGGING **************************** """


if __name__ == "__main__":
    preparation()

    stdscr = curses.initscr()
    stdscr.keypad(True) # enable read special keys
    curses.wrapper(main)
    curses.endwin()
