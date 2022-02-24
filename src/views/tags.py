import curses
import curses.ascii
import yaml
import os


from views.filtering import filter_management
from views.help import show_help

from modules.buffer import Tags, UserInput

from utils.loading import load_tags_from_file
from utils.input import get_user_input
from utils.screens import *
from utils.printing import *
from utils.logger import *



def save_tags_to_file(tags):
    with open(tags.path, 'w+', encoding='utf8') as f:
        yaml.dump(tags.data, f, default_flow_style=False, allow_unicode=True)



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
        env.update_tagging_data(win, tags)
        rewrite_all_wins(stdscr, env)

        key = stdscr.getch()
        try:
            # ======================= EXIT =======================
            if key == curses.KEY_F10:
                tags.save_to_file()
                env.update_tagging_data(win, tags)
                env.set_exit_mode()
                return env
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                tags.save_to_file()
                env.update_tagging_data(win, tags)
                env.switch_to_next_mode()
                return env
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                env = resize_all(stdscr, env)
                screen, win = env.get_screen_for_current_mode()
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(tags, use_restrictions=False)
            elif key == curses.KEY_DOWN:
                win.down(tags, filter_on=env.tag_filter_on(), use_restrictions=False)
            # ======================= F KEYS =======================
            elif key == curses.KEY_F1: # help
                env = show_help(stdscr, env)
                screen, win = env.get_screen_for_current_mode()
                curses.curs_set(0)
            elif key == curses.KEY_F2: # edit current tag
                pass
            elif key == curses.KEY_F3: # create new tag
                title = "Enter new tag in format: tag_name param1 param2 ..."
                env, text = get_user_input(stdscr, env, title=title)
                screen, win = env.get_screen_for_current_mode()
                curses.curs_set(0)
                if text is not None:
                    tag_parts = ''.join(text).split()
                    if len(tag_parts) < 1:
                        log("unknown command, press F1 to see help")
                    else:
                        tag_name, *args = tag_parts
                        tags.set_tag(tag_name, args)
                        tags.save_to_file()
            elif key == curses.KEY_F4: # open tags file for edit
                env.update_tagging_data(win, tags)
                if not os.path.exists(tags.path):
                    with open(tags.path, 'a+') as f: pass
                env.set_view_mode()
                env.enable_file_edit()
                env.set_file_to_open(tags.path)
                return env
            elif key == curses.KEY_F8: # delete current tag
                tags.remove_tag_by_idx(win.cursor.row)
                tags.save_to_file()
                win.up(tags, use_restrictions=False)
            elif key == curses.KEY_F9: # set filter
                env = filter_management(stdscr, screen, win, env)
                env.update_tagging_data(win, tags)
                env.prepare_browsing_after_filter()
                return env
        except Exception as err:
            log("tagging | "+str(err))
            env.set_exit_mode()
            return env
