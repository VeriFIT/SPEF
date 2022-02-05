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



def tag_management(stdscr, conf):
    curses.curs_set(0)
    screen = conf.right_down_screen
    win = conf.right_down_win


    """ read tags from file """
    if conf.tags: # tag file was already loaded
        tags = conf.tags
    else:
        tags = load_tags_from_file(conf.file_to_open)
        conf.right_down_win.set_cursor(0,0)
        if tags is None:
            log("unexpected exception while load tags from file")
            conf.set_exit_mode()
            return conf
        else:
            conf.tags = tags


    while True:
        """ print all screens """
        conf.update_tagging_data(win, tags)
        rewrite_all_wins(conf)

        key = stdscr.getch()
        try:
            # ======================= EXIT =======================
            if key == curses.KEY_F10:
                tags.save_to_file()
                conf.update_tagging_data(win, tags)
                conf.set_exit_mode()
                return conf
            # ======================= FOCUS =======================
            elif key == curses.ascii.TAB:
                tags.save_to_file()
                conf.update_tagging_data(win, tags)
                conf.set_brows_mode()
                return conf
            # ======================= RESIZE =======================
            elif key == curses.KEY_RESIZE:
                conf = resize_all(stdscr, conf)
                screen, win = conf.right_down_screen, conf.right_down_win
            # ======================= ARROWS =======================
            elif key == curses.KEY_UP:
                win.up(tags, use_restrictions=False)
            elif key == curses.KEY_DOWN:
                win.down(tags, filter_on=conf.tag_filter_on(), use_restrictions=False)
            # ======================= F KEYS =======================
            elif key == curses.KEY_F1: # help
                conf = show_help(stdscr, conf)
                screen, win = conf.right_down_screen, conf.right_down_win
                curses.curs_set(0)
            # elif key == curses.KEY_F2: # edit current tag
            elif key == curses.KEY_F3: # create new tag
                title = "Enter new tag in format: tag_name param1 param2 ..."
                conf, text = get_user_input(stdscr, conf, title=title)
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
                conf.update_tagging_data(win, tags)
                if not os.path.exists(tags.path):
                    with open(tags.path, 'a+') as f: pass
                conf.set_view_mode()
                conf.enable_file_edit()
                conf.set_file_to_open(tags.path)
                return conf
            elif key == curses.KEY_F8: # delete current tag
                tags.remove_tag_by_idx(win.cursor.row)
                tags.save_to_file()
                win.up(tags, use_restrictions=False)
            elif key == curses.KEY_F9: # set filter
                conf = filter_management(stdscr, screen, win, conf)
                """ rewrite screen in case that windows were resized during filter mgmnt """
                # show_tags(conf.right_down_screen, conf.right_down_win, tags, conf)
                conf.update_tagging_data(win, tags)
                conf.set_brows_mode()
                conf.quick_view = True
                conf.left_win.reset_shifts()
                conf.left_win.set_cursor(0,0)
                return conf
        except Exception as err:
            log("tagging | "+str(err))
            conf.set_exit_mode()
            return conf