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
from utils.parsing import parse_solution_info_visualization, parse_solution_info_predicate


""" represents content of current working directory (cwd)"""
class Directory:
    def __init__(self, path, dirs=None, files=None):
        self.path = path
        self.dirs = [] if dirs is None else dirs
        self.files = [] if files is None else files

        self.proj = None # None or project object (if its project subdirectory)
        self.dirs_info = None # {"dir_name1"=[info1, info2, "   ", info4], "dir_name2"=[...]}

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

    def get_dirs_info(self, env):
        is_root_proj = False
        if is_root_project_dir(self.path):
            is_root_proj = True

        result = {}
        for dir_name in self.dirs:
            infos = None
            dir_path = os.path.join(self.path, dir_name)
            if self.proj is not None:
                if is_root_proj and match_regex(self.proj.solution_id, dir_name):
                    # IS SOLUTION DIR
                    infos = self.get_info_for_solution(env, self.proj, dir_path)
                elif is_testcase_result_dir(self.proj.solution_id, dir_path):
                    # IS TESTCASE DIR
                    solution_dir = os.path.dirname(os.path.dirname(dir_path))
                    infos = self.get_info_for_solution(env, self.proj, solution_dir, info_for_tests=True, test_name=dir_name)

            result[dir_name] = infos
        self.dirs_info = result

    def get_info_for_solution(self, env, proj, solution_dir, info_for_tests=False, test_name=None):
        try:
            # get required info for project
            if info_for_tests:
                solution_info = proj.get_only_valid_tests_info()
            else:
                solution_info = proj.get_only_valid_solution_info()
            if not solution_info:
                return []

            result = []
            infos_dict = {} # 'identifier' = (match, visualization, color)
            solution_info = sorted(solution_info, key=lambda d: d['identifier'])

            for info in solution_info:
                identifier = info['identifier']
                predicates = info['predicates']

                # parse visualization and length
                visualization, length = parse_solution_info_visualization(info, solution_dir)

                # check predicates and get color
                if length is not None:
                    color = curses.A_NORMAL
                    if visualization is None:
                        match, visual = False, ' '*length
                    else:
                        predicate_matches = False if len(predicates)>0 else True
                        for predicate in predicates:
                            # match first predicate and get its color
                            predicate_matches, col = parse_solution_info_predicate(predicate, solution_dir, info_for_tests=info_for_tests, test_name=test_name)
                            if predicate_matches:
                                color = col
                                break
                        match = predicate_matches
                        visual = visualization if match else ' '*length

                    if identifier not in infos_dict:
                        infos_dict[identifier] = (match, visual, color)
                    else:
                        # if there is more than one info with this identifier
                        last_match, _, _ = infos_dict[identifier]
                        if not last_match: # if the last one failed to match, add second one
                            infos_dict[identifier] = (match, visual, color)

            for info in infos_dict:
                _, visual, color = infos_dict[info]
                result.append((visual, color))

            return result
        except Exception as err:
            log("get info for solution | "+str(err))
            return []

