import os
import glob
import fnmatch
import json
import re
import traceback
import datetime

from modules.buffer import UserInput
from modules.tags import Tags
from modules.project import Project

from utils.loading import *
from utils.logger import *
from utils.match import *


""" represents content of current working directory (cwd)"""
class Directory:
    def __init__(self, path, dirs=None, files=None):
        self.path = path
        self.dirs = [] if dirs is None else dirs
        self.files = [] if files is None else files

        self.proj = None # None or project object (if its project subdirectory)


    def __len__(self):
        return len(self.dirs) + len(self.files)

    def is_empty(self):
        return not (self.dirs or self.files)
 
    """ returns dirs and files currently displayed due to a shift in the browsing window"""
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

    """ returns list of all items (directories and files) in current working directory"""
    def get_all_items(self):
        items = self.dirs.copy()
        items.extend(self.files)
        return items

    def get_proj_conf(self):
        try:
            proj_path = get_proj_path(self.path)
            if proj_path is not None:
                proj_data = load_proj_from_conf_file(proj_path)
                # create Project obj from proj data
                self.proj = Project(proj_path)
                succ = self.proj.set_values_from_conf(proj_data)
                if not succ:
                    self.proj = None
        except Exception as err:
            log("get proj conf | "+str(err)+" | "+str(traceback.format_exc()))



