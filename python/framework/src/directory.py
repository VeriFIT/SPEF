import os
import glob
import fnmatch
import yaml
import re

from logger import *
from buffer import Tags, UserInput


""" represents content of current working directory """
class Directory:
    def __init__(self, path, dirs=[], files=[]):
        self.path = path
        self.dirs = dirs
        self.files = files


    def __len__(self):
        return len(self.dirs) + len(self.files)

    def is_empty(self):
        return not (self.dirs or self.files)
 
    def get_shifted_dirs_and_files(self, shift):
        if shift > 0:
            dirs_count = len(self.dirs)
            if shift == dirs_count:
                dirs = []
                files = self.files
            elif shift > dirs_count:
                dirs = []
                files = self.files[(shift-dirs_count):]
            else:
                dirs = self.dirs[shift:]
                files = self.files
            return dirs, files
        else:
            return self.dirs, self.files

    def get_all_items(self):
        items = self.dirs.copy()
        items.extend(self.files)
        return items


class Filter:
    def __init__(self, project_path):
        self.project_path = project_path

        self.path = None
        self.content = None
        self.tag = None

        self.files = []

    def is_empty(self):
        return not (self.path or self.content or self.tag)

    def add_path(self, path):
        self.path = path

    def add_content(self, content):
        self.content = content

    def add_tag(self, tag):
        self.tag = tag

    def find_files(self, conf):
        matches = []

        if self.path:
            try:
                path_matches = []
                dest_path = os.path.join(self.project_path, "**", self.path)
                for file_path in glob.glob(dest_path, recursive=True):
                    if os.path.isfile(file_path):
                        path_matches.append(file_path)
                """
                for root, dirnames, filenames in os.walk(self.project_path):
                    for filename in fnmatch.filter(filenames, self.path):
                        file_path = os.path.join(root, filename)
                        file_name = os.path.relpath(file_path, self.project_path)
                        matches.append(file_name)
                """
                matches = path_matches
            except Exception as err:
                log("Filter by path | "+str(err))

        if self.content:
            try:
                content_matches = []
                if self.path:
                    files = matches
                else:
                    files = []
                    for root, dirnames, filenames in os.walk(self.project_path):
                        files.extend(os.path.join(root, filename) for filename in filenames)

                for file_path in files:
                    with open(file_path) as f:
                        if self.content in f.read():
                            content_matches.append(file_path)
                matches = content_matches
            except Exception as err:
                log("Filter by content | "+str(err))

        if self.tag:
            try:
                tag_matches = []
                if self.path or self.content:
                    files = matches
                else:
                    files = []
                    for root, dirnames, filenames in os.walk(self.project_path):
                        files.extend(os.path.join(root, filename) for filename in filenames)

                """ parse tag """
                # self.tag = "#test1(0,.*,2,[0-5],5)"
                tag_parsing_ok = False
                if re.match('#\w(...)',self.tag):
                    components = re.split('[#()]',self.tag)
                    if components[0]=='' and components[-1]=='':
                        components = components[1:-1]
                        if len(components)==2:
                            tag_name, args = components
                            compare_args = list(map(str, args.split(',')))
                            tag_parsing_ok = True
                if not tag_parsing_ok:
                    user_input = UserInput()
                    user.input.text = "invalid input for tag filter... press F1 to see how to use tag filter "
                    max_cols = conf.right_down_win.end_x - conf.right_down_win.begin_x
                    max_rows = conf.right_down_win.end_y - conf.right_down_win.begin_y - 1
                    show_filter(conf.right_down_screen, user_input, max_rows, max_cols, conf)
                else:
                    for file_path in files:
                        # file_name = os.path.basename(file_path)
                        # tag_path = os.path.join(TAG_DIR, str(file_name))
                        # tag_file = os.path.splitext(tag_path)[0]+".json"
                        file_name = os.path.splitext(file_path)[:-1]
                        tag_file = str(os.path.join(*file_name))+"_tags.yaml"
                        try:
                            with open(tag_file, 'r') as f:
                                data = yaml.safe_load(f)
                            tags = Tags(tag_file, data)
                        except Exception:
                            continue

                        if tags.find(tag_name, compare_args):
                            tag_matches.append(file_path)
                    matches = tag_matches
            except Exception as err:
                log("Filter by tag | "+str(err))

        filtered_files = []
        for file_path in matches:
            file_name = os.path.relpath(file_path, self.project_path)
            filtered_files.append(file_name)
        filtered_files.sort()
        self.files = filtered_files

    def reset_all(self):
        self.path = None
        self.content = None
        self.tag = None

    def reset_by_current_mode(self, conf):
        if conf.is_brows_mode():
            self.path = None
        if conf.is_view_mode():
            self.content = None
        if conf.is_tag_mode():
            self.tag = None

    def add_by_current_mode(self, conf, text):
        if conf.is_brows_mode():
            self.path = text
        if conf.is_view_mode():
            self.content = text
        if conf.is_tag_mode():
            self.tag = text
