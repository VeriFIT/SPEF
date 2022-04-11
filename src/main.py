#!/usr/bin/env python3

import curses
import curses.ascii
import datetime
import json
import yaml
import os
import re
import io
import sys
import fnmatch
import glob
import time
import threading
import select
import signal


from views.browsing import get_directory_content, directory_browsing
from views.filtering import filter_management
from views.viewing import file_viewing
from views.tags import tag_management
from views.notes import notes_management

from views.help import show_help

from modules.environment import Environment, BASH_CMD, BASH_EXE
from modules.buffer import Buffer, Report, UserInput
from modules.directory import Directory
from modules.window import Window, Cursor

from utils.loading import *
from utils.screens import *
from utils.coloring import *
from utils.printing import *
from utils.logger import *


global bash_proc


"""
- set ncurses settings
- returns env object with
    * created screens and windwos for ncurese
    * loaded config from file
    * loaded controls from file
    * loaded typical notes from file

"""
def prepare_environment(stdscr):
    curses.set_escdelay(1)

    """ set coloring """
    curses.start_color()
    curses.use_default_colors()

    init_color_pairs()
    bkgd_color = curses.color_pair(COL_BKGD)
    stdscr.bkgd(' ', bkgd_color)

    """ create screens and windows for TUI """
    screens, windows = create_screens_and_windows(curses.LINES, curses.COLS)
    windows.brows.set_cursor(0,0)
    windows.notes.set_cursor(0,0)
    windows.tag.set_cursor(0,0)

    """ load config from file and create framework environment """
    config = load_config_from_file()
    if config is None:
        return None
    env = Environment(screens, windows, config)

    """ load control from file """
    control = load_control_from_file()
    if control is None:
        return None
    env.set_user_control(control)

    """ load saved typical notes from file """
    env.typical_notes = load_typical_notes_from_file()

    """ get current files and dirs """
    env.cwd = get_directory_content(env)
    return env



""" ======================= START MAIN ========================= """
def main(stdscr):
    global bash_proc
    log("START")

    """ prepare env from configuration files """
    env = prepare_environment(stdscr)
    if env is None:
        bash_proc.stop()
        exit(-1)

    """ show all main screens """
    stdscr.clear()
    stdscr.erase()
    stdscr.refresh()
    refresh_main_screens(env)

    """ main loop """
    while True:
        if env.bash_active:
            if env.bash_function == BASH_CMD:
                env = run_in_bash(stdscr, env, env.bash_cmd)
                # show_in_bash(stdscr, env, "echo hallo...\n")
            elif env.bash_function == BASH_EXE:
                env = executing_bash(stdscr, env)
            else:
                env.bash_active = False
        else:
            print_hint(env)
            if env.is_exit_mode():
                bash_proc.set_reader(False)
                break
            elif env.is_brows_mode():
                env = directory_browsing(stdscr, env)
            elif env.is_view_mode():
                env = file_viewing(stdscr, env)
            elif env.is_tag_mode():
                env = tag_management(stdscr, env)
            elif env.is_notes_mode():
                env = notes_management(stdscr, env)

    """ save typical notes to file """
    save_typical_notes_to_file(env.typical_notes)

    log("END")
""" ======================= END MAIN ========================= """


class Bash_process():
    def __init__(self, pid, fd, cwd):
        self.pid = pid # pid for bash subprocess
        self.fd = fd

        self.buff_lock = threading.Lock()
        self.buff = "" # bash buffer

        self.cwd = cwd
        self.active = False # bash is active
        self.reader_run = True
        self.pause = False

    def set_active(self, mode):
        with self.buff_lock:
            self.active = mode
            if mode == True:
                os.system("clear")
                print(self.buff, end="", flush=True)


    def set_reader(self, mode):
        with self.buff_lock:
            self.reader_run = mode

    def print_buff(self):
        with self.buff_lock:
            print(self.buff, end="", flush=True)

    def write_command(self, cmd):
        os.write(self.fd, cmd.encode("utf-8"))


    def async_reader(self):
        while self.reader_run:
            r, _, _ = select.select([self.fd], [], [], 1)
            if self.fd in r:
                # read from bash and save it to bash buffer
                data = os.read(self.fd, 1024)
                with self.buff_lock:
                    self.buff += data.decode("utf-8")

                    if self.active:
                        # if bash is active print bash
                        print(data.decode("utf-8"), end="", flush=True)

    def stop(self):
        self.set_reader(False)
        os.system(f"kill {self.pid}") # os.kill(self.pid)

    def signal_handler(self, sig, frame):
        self.stop()
        sys.exit(0)



""" switch to bash """
def executing_bash(stdscr, env):
    global bash_proc 

    # go to current working direcotry
    if bash_proc.cwd != env.cwd.path:
        bash_proc.write_command(f"cd {env.cwd.path}\n")
        bash_proc.cwd = env.cwd.path

    # set bash as active (rewrite screen with bash buffer)
    bash_proc.set_active(True)
    curses.curs_set(1) # set cursor as visible

    # set exit key from env (else CTRL+O by default (like in mc))
    exit_key = env.bash_exit_key if env.bash_exit_key is not None else '0f'

    # bash loop
    while True:
        c = sys.stdin.read(1)
        hex_c = c.encode("utf-8").hex()

        # exit bash
        if hex_c == exit_key:
            # set bash as inactive
            bash_proc.set_active(False)
            env.bash_active = False

            # rewrite screen with ncurses
            os.system("clear")
            stdscr.clear()
            stdscr.erase()
            stdscr.refresh()
            refresh_main_screens(env)
            rewrite_all_wins(env)
            return env
        else:
            # os.write(bash_proc.fd, c.encode("utf-8"))
            bash_proc.write_command(c)



""" run command in bash """
def run_in_bash(stdscr, env, cmd):
    global bash_proc

    # write cmd in bash
    bash_proc.write_command(cmd)

    # rewrite screen with bash buffer (show in bash)
    bash_proc.set_active(True)

    # wait for any char
    c = sys.stdin.read(1)

    # go back and rewrtie screen with ncurses
    env.bash_active = False
    bash_proc.set_active(False)

    os.system("clear")
    stdscr.clear()
    stdscr.erase()
    stdscr.refresh()
    refresh_main_screens(env)
    rewrite_all_wins(env)
    return env



""" ======================================================================= """

# TODO: cache all tags and reports to local files TAG_DIR and REPORT_DIR
def preparation():
    """ clear log file """
    with open(LOG_FILE, 'w+'): pass

    """ create dirs for tags and reports """
    if not os.path.exists(TAG_DIR):
        os.makedirs(TAG_DIR)



if __name__ == "__main__":
    # clear log file
    with open(LOG_FILE, 'w+'): pass

    # prepare bash subprocess
    pid, fd = os.forkpty()
    cwd = os.getcwd()
    bash_proc = Bash_process(pid, fd, cwd)

    # set signal handler
    signal.signal(signal.SIGINT, bash_proc.signal_handler)
    signal.signal(signal.SIGABRT, bash_proc.signal_handler)
    signal.signal(signal.SIGHUP, bash_proc.signal_handler)
    signal.signal(signal.SIGTERM, bash_proc.signal_handler)
    # signal.signal(signal.SIGQUIT, bash_proc.signal_handler)

    if pid == 0:
        # ======= child =======
        os.system("stdbuf -i0 -o0 -e0 bash") # bash without buffering stdin, stdout, stderr
    else:
        # ====== parent ======
        # thread for reading bash output and save it to buffer
        th = threading.Thread(target=bash_proc.async_reader)
        th.start()

        # run ncurses main function
        stdscr = curses.initscr()
        stdscr.keypad(True) # enable read special keys
        curses.wrapper(main)
        curses.endwin()

        th.join()
        bash_proc.set_reader(False)
        os.system(f"kill {pid}")

