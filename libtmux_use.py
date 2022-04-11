#!/usr/bin/env python3

import curses
import curses.ascii
import datetime
import json
import yaml
import os
import re
import sys
import fnmatch
import glob
import logging

import libtmux
import time

import threading
import io
import select
import signal


global bash_proc



class Bash_process():
    def __init__(self, pid, fd):
        # bash subprocess
        self.pid = pid
        self.fd = fd

        # bash buffer
        self.buff = ""
        self.reader_run = True

        # bash is active
        self.active = False

    def async_reader(self):
        # print("starting async reader")
        fd = self.fd

        while self.reader_run:
            r, _, _ = select.select([fd], [], [], 1)
            if fd in r:
                data = os.read(fd, 1024)
                self.buff += data.decode("utf-8")
                if self.active:
                    print(data.decode("utf-8"), end="", flush=True)

    def signal_handler(self, sig, frame):
        # global bash_proc
        os.system(f"kill {self.pid}")
        sys.exit(0)



def main(stdscr):
    global bash_proc

    curses.set_escdelay(1)

    # rewrite
    stdscr.clear()
    stdscr.addstr(5, 5, "HELLO !!!", curses.A_NORMAL)
    stdscr.refresh()
    curses.start_color()
    curses.use_default_colors()
    stdscr.bkgd(' ', curses.A_NORMAL)
    stdscr.refresh()

    while(True):
        key = stdscr.getch()

        # rewrite
        stdscr.clear()
        stdscr.addstr(5, 5, "HELLO !!!", curses.A_NORMAL)
        stdscr.refresh()
        if key == 27:
            bash_proc.reader_run = False
            return
        elif key == curses.KEY_F1:

            bash_proc.active = True
            os.system("clear")
            print(bash_proc.buff, end="", flush=True)
            while True:
                # b = stdscr.getch()
                b = sys.stdin.read(1)

                # if chr(b) != '0':
                if b != '0':
                    # os.write(bash_proc.fd, curses.ascii.ascii(b).to_bytes()) # TODO: check if 'b' is ascii char
                    os.write(bash_proc.fd, b.encode("utf-8"))
                else:
                    bash_proc.active = False
                    os.system("clear")

                    # stdscr = curses.initscr()
                    stdscr.clear()
                    stdscr.erase()
                    stdscr.addstr(5, 5, "HELLO !!!", curses.A_NORMAL)
                    stdscr.refresh()
                    break



if __name__ == "__main__":

    pid, fd = os.forkpty()
    bash_proc = Bash_process(pid, fd)


    # TODO: odchytit ctrl+c (signal vseobecne) --> kill pid (SIGINT SIGTERM SIGABRT SIGHUB)
    signal.signal(signal.SIGINT, bash_proc.signal_handler)


    if pid == 0:
        print("child start")
        # os.system("bash") # os.system("stdbuf -i0 -o0 -e0 bash")
        os.system("stdbuf -i0 -o0 -e0 bash")
    else:
        th = threading.Thread(target=bash_proc.async_reader)
        th.start()
        time.sleep(3)


        stdscr = curses.initscr()
        stdscr.keypad(True) # enable read special keys
        curses.wrapper(main)
        curses.endwin()

        th.join()
        os.system(f"kill {pid}")


    # server = libtmux.Server()
    # print(server)

    # try:
        # session = server.find_where({"session_name": "test"})
    # except:
        # session = server.new_session("test")

    # session = server.find_where({"session_name": "test"})
    
    # print(server)
    # print(server.list_sessions())
    # print(server.get_by_id('$0'))

    # new window
    # win = session.new_window(attach=False, window_name="foo_win")
    # win.kill_window()
    # session.kill_window("foo_win")


    # get window and rename it
    # win1 = session.attached_window # return window = dp_win
    # win1.rename_window("ncurses") # dp_win --> ncurses

    # win2 = session.new_window('tmp_win')
    # print(session.attached_window) # tmp_win

    # ******** in tmp_win ********
    # win = session.find_where({"window_name": "tmp_win"})
    # win.select_window()
    # pane = session.attached_pane
    # pane.send_keys('echo hello')


    # ******** in ncurses ********
    # win = session.find_where({"window_name": "ncurses"})
    # win.select_window()
    # pane = session.attached_pane
    # pane.send_keys('read')


    # ******** in tmp_win ********
    # win = session.find_where({"window_name": "tmp_win"})
    # win.select_window()

    # exit()

    # split window to pane
    # pane = window.split_window(attach=False) # split window dp_win
    # pane.select_pane() # switch to splited window
    # pane = session.attached_pane
    # print(pane)


    # window = session.new_window(attach=False, window_name="next_win") # return window = next_win
    # pane = window.split_window(attach=False) # split window next_win

    # print to pane
    # pane.send_keys('echo hello...', enter=False)
    # pane.enter()
    # pane.send_keys('echo hello')

    # pane.clear()
    # pane.send_keys('cowsay hello')
    # print('\n'.join(pane.cmd('capture-pane', '-p').stdout))

    # print(pane.window)
    # print(pane.window.session)

