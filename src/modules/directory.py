import os
import glob
import fnmatch
import json
import re
import traceback
import datetime

from modules.buffer import Tags, UserInput

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
            cur_dir = self.path
            while True:
                file_list = os.listdir(cur_dir)
                parent_dir = os.path.dirname(cur_dir)
                if PROJECT_FILE in file_list:
                    proj_data = load_proj_from_conf_file(cur_dir)

                    """ create Project obj from proj data """
                    self.proj = Project(cur_dir)
                    self.proj.set_values_from_conf(proj_data)
                    return
                else:
                    if cur_dir == parent_dir:
                        return
                    else:
                        cur_dir = parent_dir
        except Exception as err:
            log("get proj conf | "+str(err)+" | "+str(traceback.format_exc()))



class Project:
    def __init__(self, path):
        self.path = path
        self.created = None
        self.tests_dir = None
        self.solution_id = None
        self.solution_type_dir = True # True = solution id matches directory, False = solution id matches file

        self.sut_required = ""
        self.sut_ext_variants = []

        self.description = ""
        self.test_timeout = 0
        self.solutions_dir = None
        self.solution_quick_view = None
        self.solution_test_quick_view = None

    def set_values_from_conf(self, data):
        try:
            self.created = data['created']
            self.tests_dir = data['tests_dir']
            self.solution_id = data['solution_id']
            self.solution_type_dir = data['solution_type_dir']
            self.sut_required = data['sut_required']
            self.sut_ext_variants = data['sut_ext_variants']
        except:
            log("wrong data for proj")


    def set_default_values(self):
        self.created = datetime.date.today() # date of creation
        self.tests_dir = "tests"
        self.solution_id =  "x[a-z]{5}[0-9]{2}" # default solution identifier: xlogin00
        self.solution_type_dir = True # default solution type is directory
        self.sut_required = "sut" # default file name of project solution is "sut" (system under test)
        self.sut_ext_variants = ["*sut*", "sut.sh", "sut.bash"]


        self.test_timeout = 5
        self.solutions_dir = "solutions"
        self.solution_quick_view = "auto_report"
        self.solution_test_quick_view = "stdout"


    def to_dict(self):
        return {
            'created': self.created,
            'tests_dir': self.tests_dir,
            'solution_id': self.solution_id,
            'solution_type_dir': self.solution_type_dir,
            'sut_required': self.sut_required,
            'sut_ext_variants': self.sut_ext_variants
        }
        #     'tests_dir': self.tests_dir
        #     'test_timeout': self.test_timeout
        #     'solutions_dir': self.solutions_dir
        #     'solution_id': self.solution_id
        #     'solution_quick_view': self.solution_quick_view
        #     'solution_test_quick_view': self.solution_test_quick_view
        # }



""" class for currently set filters (by path, file content or tag) """
class Filter:
    def __init__(self, project):
        self.project = project # search for filtered files only in current project

        self.path = None
        self.content = None
        self.tag = None

        self.files = []

    def is_empty(self):
        return not (self.path or self.content or self.tag)

    """ add filter by path """
    def add_path(self, path):
        self.path = path

    """ add filter by file content """
    def add_content(self, content):
        self.content = content

    """ add filter by tag """
    def add_tag(self, tag):
        self.tag = tag


    """ search for files with match of all set filters in project directory """
    def find_files(self, env):
        matches = []

        if self.path:
            matches = self.get_files_by_path(self.project, self.path)

        if self.content:
            # if some filtering has already been done, search for files only in its matches
            # else search all files in project directory
            files = matches if self.path else self.get_files_in_dir_recursive(self.project)
            matches = self.get_files_by_content(files)

        if self.tag:
            files = matches if (self.path or self.content) else self.get_files_in_dir_recursive(self.project)
            matches = self.get_files_by_tag(files)

        filtered_files = []
        for file_path in matches:
            file_name = os.path.relpath(file_path, self.project)
            filtered_files.append(file_name)
        filtered_files.sort()
        self.files = filtered_files


    """ remove all filteres """
    def reset_all(self):
        self.path = None
        self.content = None
        self.tag = None


    """ remove filter according to current mode (ex: if broswing, remove filter by path) """
    def reset_by_current_mode(self, env):
        if env.is_brows_mode():
            self.path = None
        if env.is_view_mode():
            self.content = None
        if env.is_tag_mode():
            self.tag = None


    """ set filter according to current mode """
    def add_by_current_mode(self, env, text):
        if env.is_brows_mode():
            self.path = text
        if env.is_view_mode():
            self.content = text
        if env.is_tag_mode():
            self.tag = text



    """ returns list of all files in directory (recursive) """
    def get_files_in_dir_recursive(self, dir_path):
        files = []
        for root, dirnames, filenames in os.walk(dir_path):
            files.extend(os.path.join(root, filename) for filename in filenames)
        return files


    """ 
    src: source directory path
    dest: destination path to match
    """
    def get_files_by_path(self, src, dest):
        try:
            path_matches = []
            dest_path = os.path.join(src, "**", dest+"*")
            for file_path in glob.glob(dest_path, recursive=True):
                if os.path.isfile(file_path):
                    path_matches.append(file_path)
            return path_matches
        except Exception as err:
            log("Filter by path | "+str(err)+" | "+str(traceback.format_exc()))
            return []


    """ 
    files: files to filter
    content: content to match
    """
    def get_files_by_content(self, files):
        try:
            content_matches = []
            for file_path in files:
                with open(file_path) as f:
                    if self.content in f.read():
                        content_matches.append(file_path)
            return content_matches
        except Exception as err:
            log("Filter by content | "+str(err)+" | "+str(traceback.format_exc()))
            # if there is some exception, dont apply filter, just ignore it and return all files
            return files


    """
    files: files to filter
    tag: tag to match, ex: "test1(0,.*,2,[0-5],5)"
    """
    def get_files_by_tag(self, files):
        try:
            tag_matches = []

            """ parse tag """
            tag_parsing_ok = False
            if re.match('\w(...)', self.tag):
                components = re.split('[()]', self.tag)
                # log(components)
                if len(components)>0:
                    # search only for tag name
                    tag_name = components[0]
                    compare_args = None
                    tag_parsing_ok = True
                    if len(components)>1 and components[1]!="":
                        compare_args = list(map(str, components[1].split(',')))

            if not tag_parsing_ok:
                log("invalid input for tag filter")
                return files
            else:
                for file_path in files:
                    tags = load_tags_from_file(file_path)
                    if tags and len(tags)>0:
                        if tags.find(tag_name, compare_args):
                            tag_matches.append(file_path)
                return tag_matches
        except Exception as err:
            log("Filter by tag | "+str(err)+" | "+str(traceback.format_exc()))
            return files
