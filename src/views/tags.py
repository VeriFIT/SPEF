import curses
import curses.ascii
import yaml
import os
import traceback

from controls.control import *

from views.filtering import filter_management
from views.help import show_help
from views.input import get_user_input

from modules.buffer import Tags, UserInput

from utils.loading import load_tags_from_file, save_tags_to_file
from utils.screens import *
from utils.printing import *
from utils.logger import *


def tag_management(stdscr, env):
    curses.curs_set(0)
    screen, win = env.get_screen_for_current_mode()

    """ read tags from file """
    if env.tags: # tag file was already loaded
        tags = env.tags
    else:
        tags = load_tags_from_file(env.file_to_open)
        # win.reset(0,0)
        if tags is None:
            log("unexpected exception while load tags from file")
            env.set_exit_mode()
            return env
        else:
            env.tags = tags


    while True:
        """ print all screens """
        # screen, win = env.get_screen_for_current_mode()
        rewrite_all_wins(env)

        key = stdscr.getch()

        try:
            function = get_function_for_key(env, key)
            if function is not None:
                env, exit_program = run_function(stdscr, env, function, key)
                if exit_program:
                    return env

        except Exception as err:
            log("tagging | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env



""" implementation of functions for tag management """
def run_function(stdscr, env, fce, key):
    screen, win = env.get_screen_for_current_mode()

    # ======================= EXIT =======================
    if fce == EXIT_PROGRAM:
        env.tags.save_to_file()
        env.set_exit_mode()
        return env, True
    # ======================= FOCUS =======================
    elif fce == CHANGE_FOCUS:
        env.tags.save_to_file()
        env.switch_to_next_mode()
        return env, True
    # ======================= RESIZE =======================
    elif fce == RESIZE_WIN:
        env = resize_all(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
    # ======================= ARROWS =======================
    elif fce == CURSOR_UP:
        win.up(env.tags, use_restrictions=False)
    elif fce == CURSOR_DOWN:
        win.down(env.tags, filter_on=env.tag_filter_on(), use_restrictions=False)
    # ======================= SHOW HELP =======================
    elif fce == SHOW_HELP:
        env = show_help(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
    # ======================= EDIT TAG =======================
    elif fce == EDIT_TAG:
        # get current tag
        tag_name, args = env.tags.get_tag_by_idx(win.cursor.row)

        if tag_name is not None:
            user_input = UserInput()
            user_input.text = list(f"{tag_name} {' '.join(args)}")

            # get new tag (edited)
            title = "Edit tag in format: tag_name param1 param2 ..."
            env, text = get_user_input(stdscr, env, title=title, user_input=user_input)
            if env.is_exit_mode():
                return env, True
            screen, win = env.get_screen_for_current_mode()
            curses.curs_set(0)

            # replace old tag with new one 
            if text is not None:
                tag_parts = ''.join(text).split()
                if len(tag_parts) < 1:
                    log("edit tag | wrong tag format")
                else:
                    # remove old tag
                    env.tags.remove_tag_by_idx(win.cursor.row)
                    # add new tag
                    tag_name, *args = tag_parts
                    env.tags.set_tag(tag_name, args)
                    env.tags.save_to_file()
    # ======================= ADD TAG =======================
    elif fce == ADD_TAG:
        title = "Enter new tag in format: tag_name param1 param2 ..."
        env, text = get_user_input(stdscr, env, title=title)
        if env.is_exit_mode():
            return env, True
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
        if text is not None:
            tag_parts = ''.join(text).split()
            if len(tag_parts) < 1:
                log("add tag | wrong tag format")
            else:
                tag_name, *args = tag_parts
                env.tags.set_tag(tag_name, args)
                env.tags.save_to_file()
    # ======================= OPEN FILE TAG =======================
    elif fce == OPEN_TAG_FILE:
        pass
    # ======================= DELETE TAG =======================
    elif fce == DELETE_TAG:
        env.tags.remove_tag_by_idx(win.cursor.row)
        env.tags.save_to_file()
        win.up(env.tags, use_restrictions=False)
    # ======================= FILTER =======================
    elif fce == FILTER:
        env = filter_management(stdscr, screen, win, env)
        if env.is_exit_mode() or env.is_brows_mode():
            return env, True
        curses.curs_set(0)


    env.update_win_for_current_mode(win)
    return env, False
