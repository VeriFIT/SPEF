import curses
import curses.ascii
import shlex
import traceback

import spef.controls.functions as func
from spef.controls.control import get_function_for_key
from spef.modules.buffer import UserInput
from spef.modules.bash import Bash_action
from spef.utils.loading import save_tags_to_file
from spef.utils.screens import resize_all
from spef.utils.printing import rewrite_all_wins
from spef.utils.logger import log
from spef.views.filtering import filter_management
from spef.views.help import show_help
from spef.views.input import get_user_input


def tag_management(stdscr, env):
    curses.curs_set(0)
    screen, win = env.get_screen_for_current_mode()

    if env.tags is None:  # there is no tags loaded
        env.switch_to_next_mode()
        return env

    while True:
        """print all screens"""
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
            log("tagging | " + str(err) + " | " + str(traceback.format_exc()))
            env.set_exit_mode()
            return env


""" implementation of functions for tag management """


def run_function(stdscr, env, fce, key):
    screen, win = env.get_screen_for_current_mode()

    # ======================= EXIT =======================
    if fce == func.EXIT_PROGRAM:
        save_tags_to_file(env.tags)
        env.set_exit_mode()
        return env, True
    # ======================= BASH =======================
    elif fce == func.BASH_SWITCH:
        hex_key = "{0:x}".format(key)
        env.bash_action = Bash_action()
        env.bash_action.set_exit_key(("0" if len(hex_key) % 2 else "") + str(hex_key))
        env.bash_active = True
        return env, True
    # ======================= FOCUS =======================
    elif fce == func.CHANGE_FOCUS:
        save_tags_to_file(env.tags)
        env.switch_to_next_mode()
        return env, True
    # ======================= RESIZE =======================
    elif fce == func.RESIZE_WIN:
        env = resize_all(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
    # ======================= ARROWS =======================
    elif fce == func.CURSOR_UP:
        win.up(env.tags, use_restrictions=False)
    elif fce == func.CURSOR_DOWN:
        win.down(env.tags, filter_on=env.tag_filter_on(), use_restrictions=False)
    # ======================= SHOW HELP =======================
    elif fce == func.SHOW_HELP:
        show_help(stdscr, env)
        curses.curs_set(0)
    # ======================= EDIT TAG =======================
    elif fce == func.EDIT_TAG:
        # get current tag
        tag_name, old_args = env.tags.get_tag_by_idx(win.cursor.row)

        if tag_name is not None:
            user_input = UserInput()
            args = [f"'{arg}'" for arg in old_args]
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
                tag_parts = shlex.split("".join(text))
                # tag_parts = ''.join(text).split()
                if len(tag_parts) < 1:
                    log("edit tag | wrong tag format")
                else:
                    # remove old tag
                    env.tags.remove_tag_by_idx(win.cursor.row)
                    # add new tag
                    new_tag_name, *new_args = tag_parts
                    succ = env.tags.set_tag(new_tag_name, new_args)
                    if not succ:
                        env.tags.set_tag(tag_name, old_args)
                    save_tags_to_file(env.tags)
    # ======================= ADD TAG =======================
    elif fce == func.ADD_TAG:
        title = "Enter new tag in format: tag_name param1 param2 ..."
        env, text = get_user_input(stdscr, env, title=title)
        if env.is_exit_mode():
            return env, True
        screen, win = env.get_screen_for_current_mode()
        curses.curs_set(0)
        if text is not None:
            tag_parts = shlex.split("".join(text))
            if len(tag_parts) < 1:
                log("add tag | wrong tag format")
            else:
                tag_name, *args = tag_parts
                env.tags.set_tag(tag_name, args)
                save_tags_to_file(env.tags)
    # ======================= OPEN FILE TAG =======================
    elif fce == func.OPEN_TAG_FILE:
        pass
    # ======================= DELETE TAG =======================
    elif fce == func.DELETE_TAG:
        env.tags.remove_tag_by_idx(win.cursor.row)
        save_tags_to_file(env.tags)
        win.up(env.tags, use_restrictions=False)
    # ======================= FILTER =======================
    elif fce == func.FILTER:
        env = filter_management(stdscr, screen, win, env)
        if env.is_exit_mode() or env.is_brows_mode():
            return env, True
        curses.curs_set(0)

    env.update_win_for_current_mode(win)
    return env, False
