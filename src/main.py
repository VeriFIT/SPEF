#!/usr/bin/env python3

import curses
import curses.ascii
import os
import select
import shutil
import signal
import sys
import termios
import threading
import time
import tty

from modules.environment import Environment
from utils.loading import *
from utils.screens import *
from utils.coloring import *
from utils.printing import *
from utils.logger import *

from views.browsing import get_directory_content, directory_browsing
from views.viewing import file_viewing
from views.tags import tag_management
from views.notes import notes_management
from views.user_logs import logs_viewing, go_down_in_user_logs


global bash_proc
INT_BASH = 5


"""
- set ncurses settings
- returns env object with
    * created screens and windows for ncurses
    * loaded config from file
    * loaded controls from file
    * loaded typical notes from file
    * loaded user logs from file
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
    print_prepare_message(stdscr, 0, "preparing screens...")
    screens, windows = create_screens_and_windows(curses.LINES, curses.COLS)
    windows.brows.set_cursor(0,0)
    windows.notes.set_cursor(0,0)
    windows.tag.set_cursor(0,0)


    """ load config from file and create framework environment """
    print_prepare_message(stdscr, 1, "preparing system environment...")
    config = load_config_from_file()
    if config is None:
        return None
    env = Environment(screens, windows, config)


    """ load control from file """
    print_prepare_message(stdscr, 2, "loading system controls...")
    control = load_control_from_file()
    if control is None:
        return None
    env.set_user_control(control)


    """ load saved typical notes from file """
    print_prepare_message(stdscr, 3, "loading typical notes...")
    env.typical_notes = load_typical_notes_from_file()


    """ load user logs from file """
    print_prepare_message(stdscr, 4, "loading user logs...")
    env.user_logs = load_user_logs_from_file()
    go_down_in_user_logs(env)


    """ get current files and dirs """
    env.cwd = get_directory_content(env)


    print_prepare_message(stdscr, 5, "preparing done !")
    return env


def print_prepare_message(stdscr, i, mess):
    if curses.LINES > i and curses.COLS > 0:
        stdscr.addstr(i,0,mess[:curses.COLS])
        stdscr.refresh()


""" ======================= START MAIN ========================= """
def main(stdscr, env=None):
    global bash_proc
    log("START")

    """ prepare env from configuration file """
    if env is None:
        env = prepare_environment(stdscr)
        if env is None:
            bash_proc.stop()
            exit(-1)

    env.bash_fd = bash_proc.fd

    """ show all main screens """
    stdscr.clear()
    stdscr.erase()
    stdscr.refresh()
    refresh_main_screens(env)

    """ main loop """
    while True:
        if env.bash_active:
            return INT_BASH, env
        else:
            print_hint(env)
            if env.is_exit_mode():
                try:
                    if os.path.exists(TMP_DIR):
                        shutil.rmtree(TMP_DIR)
                except Exception as err:
                    log(f"{TMP_DIR} cannot be removed | {err}")
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
            elif env.is_logs_mode():
                env = logs_viewing(stdscr, env)

    """ save typical notes to file """
    save_typical_notes_to_file(env.typical_notes)

    log("END")
    return 0, None
""" ======================= END MAIN ========================= """


class Bash_process():
    def __init__(self, pid, fd):
        self.pid = pid # pid for bash subprocess
        self.fd = fd

        self.buff_lock = threading.Lock()
        self.buff = "" # bash buffer

        self.active = False # bash is active
        self.reader_run = True
        self.pause = False

    # set bash as active (reader will print data)
    def set_active(self, mode):
        with self.buff_lock:
            self.active = mode
            if mode == True:
                # rewrite screen with bash buffer
                os.system("clear")
                print(self.buff, end="", flush=True)

    # set entry and exit condition for reader
    def set_reader(self, mode):
        with self.buff_lock:
            self.reader_run = mode

    # reader will still run but it wont save data to buffer and print it
    def pause_reader(self, mode):
        with self.buff_lock:
            self.pause = mode

    def write_command(self, cmd):
        os.write(self.fd, cmd.encode("utf-8"))


    def async_reader(self):
        while self.reader_run:
            r, _, _ = select.select([self.fd], [], [], 1)
            if self.fd in r:
                # read from bash and save it to bash buffer
                data = os.read(self.fd, 1024)
                with self.buff_lock:
                    if not self.pause:
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
    bash_proc.pause_reader(True)
    bash_proc.write_command(f"cd {env.cwd.path}\n")
    time.sleep(0.2)
    bash_proc.pause_reader(False)
    bash_proc.write_command("\n")


    # set bash as active (rewrite screen with bash buffer)
    bash_proc.set_active(True)
    # curses.curs_set(1) # set cursor as visible

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
            # stdscr.clear()
            # stdscr.erase()
            # stdscr.refresh()
            # refresh_main_screens(env)
            # rewrite_all_wins(env)
            return env
        else:
            # os.write(bash_proc.fd, c.encode("utf-8"))
            bash_proc.write_command(c)



""" run command in bash """
def run_in_bash(stdscr, env):
    global bash_proc

    if env.bash_action is None:
        env.bash_active = False
        return env

    if env.bash_action.run_in_cwd:
        # go to current working direcotry
        bash_proc.pause_reader(True)
        bash_proc.write_command(f"cd {env.cwd.path}\n")
        time.sleep(0.2)
        bash_proc.pause_reader(False)
        bash_proc.write_command("\n")

    # send command to bash
    if env.bash_action.cmd:
        bash_proc.write_command(env.bash_action.cmd+"\n")


    # rewrite screen with bash buffer (show in bash)
    bash_proc.set_active(True)
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    while True:
        # wait for any char
        c = sys.stdin.read(1)

        # if exit_key is not set, exit on any key
        if not env.bash_action.exit_key:
            exit_cond = True
        else:
            hex_c = c.encode("utf-8").hex()
            exit_cond = hex_c == env.bash_action.exit_key

        if exit_cond:
            # go back and rewrtie screen with ncurses
            env.bash_active = False
            bash_proc.set_active(False)
            os.system("clear")
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            return env
        else:
            bash_proc.write_command(c)



""" ======================================================================= """


if __name__ == "__main__":
    # clear log file
    with open(LOG_FILE, 'w+'): pass
    if not os.path.exists(TMP_DIR):
        os.mkdir(TMP_DIR)
    user_logs_file = os.path.join(DATA_DIR, USER_LOGS_FILE)
    if not os.path.exists(user_logs_file):
        with open(user_logs_file, 'w+'): pass


    # prepare bash subprocess
    pid, fd = os.forkpty()

    if pid == -1:
        log("forkpty failed")
        sys.exit(0)

    cwd = os.getcwd()
    bash_proc = Bash_process(pid, fd)

    # set signal handler
    signal.signal(signal.SIGINT, bash_proc.signal_handler)
    signal.signal(signal.SIGABRT, bash_proc.signal_handler)
    signal.signal(signal.SIGHUP, bash_proc.signal_handler)
    signal.signal(signal.SIGTERM, bash_proc.signal_handler)
    signal.signal(signal.SIGQUIT, bash_proc.signal_handler)

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
        env = None
        while True:
            ret, env = curses.wrapper(main, env)
            if ret == INT_BASH and env is not None:
                if env.bash_action is not None:
                    env = run_in_bash(stdscr, env)
                else:
                    env.bash_active = False
            else:
                break
        curses.endwin()

        th.join()
        bash_proc.set_reader(False)
        os.system(f"kill {pid}")

