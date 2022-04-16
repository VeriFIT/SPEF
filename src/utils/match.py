
import re
import os
import glob
import traceback
import tarfile
import zipfile

from utils.logger import *
# from utils.loading import *



def filter_intern_files(path_list):
    try:
        if path_list:
            # filter files with repport suffix or tags suffix
            result = list(filter(lambda x: not x.endswith((REPORT_SUFFIX, TAGS_SUFFIX)), path_list))

            # filter files from report dir and tests dir
            result = list(filter(lambda x: not match_regex(os.path.join('.*', REPORT_DIR, '.*'),x), result))
            result = list(filter(lambda x: not match_regex(os.path.join('.*', TESTS_DIR, '.*'),x), result))
            return result
    except Exception as err:
        log("filter intern files | "+str(err))
    return path_list

def match_report_dir(path):
    return match_regex(os.path.join('.*', REPORT_DIR, '.*'), path)

def match_tests_dir(path):
    return match_regex(os.path.join('.*', TESTS_DIR, '.*'), path)


############################ CHECK PATH ############################


# return True if path is a zipfile or a tarfile
def is_archive_file(path):
    if path is not None:
        if os.path.isfile(path):
            return zipfile.is_zipfile(path) or tarfile.is_tarfile(path)
    return False


# return True it path is root project directory (has proj conf file)
# ex: path = "subj1/2021/projA"           --> True
# ex: path = "subj1/2021/projA/xlogin00"  --> False
# ex: path = "subj1/2021"                 --> False
def is_root_project_dir(path):
    try:
        if path is None:
            return False

        if os.path.isdir(path):
            file_list = os.listdir(path)
            if PROJ_CONF_FILE in file_list:
                return True
        return False
    except Exception as err:
        log("is root proj dir | "+str(err))
        return False


# return True it path is some project subdirectory or file (parent has proj conf file)
# ex: path = "subj1/2021/projA/xlogin00/file1"  --> True
# ex: path = "subj1/2021/projA/xlogin00"        --> True
# ex: path = "subj1/2021/projA"                 --> True
# ex: path = "subj1/2021"                       --> False
def is_in_project_dir(path):
    try:
        if path is None:
            return False

        cur_dir = path if os.path.isdir(path) else os.path.dirname(path)
        while True:
            parent_dir = os.path.dirname(cur_dir)
            if is_root_project_dir(cur_dir):
                return True
            else:
                if cur_dir == parent_dir:
                    return False
                else:
                    cur_dir = parent_dir
    except:
        return False


# pre-condition: check if is_in_project_dir(path)
# return True it path is root solution directory (path matches solution identifier)
# ex: path = "subj1/2021/projA/xlogin00"        --> True
# ex: path = "subj1/2021/projA/xlogin00/file1"  --> False
# ex: path = "subj1/2021/projA"                 --> False
def is_root_solution_dir(solution_id, path):
    try:
        if path is None or solution_id is None:
            return False

        if os.path.isdir(path):
            parent_dir = os.path.dirname(path)
            if is_root_project_dir(parent_dir):
                return match_regex(solution_id, os.path.basename(path))
        return False
    except:
        return False


# pre-condition: check if is_in_project_dir(path)
# return True if path is file in project dir and matches solution id
def is_solution_file(solution_id, path):
    if path is not None and solution_id is not None:
        if os.path.isfile(path):
            return match_regex(solution_id, os.path.basename(path))
    return False


# pre-condition: check if is_in_project_dir(path)
# return True it path is some project solution subdirectory or file
# parent matches solution identifier
def is_in_solution_dir(solution_id, path):
    try:
        if path is None or solution_id is None:
            return False

        cur_dir = path if os.path.isdir(path) else os.path.dirname(path)
        solution_dir_found = get_parent_regex_match(solution_id, path)
        return solution_dir_found is not None
    except:
        return False


# pre-condition: check if is_in_solution_dir(path)
# return True if path is root reports dir
def is_root_reports_dir(path):
    try:
        if path is None:
            return False

        if os.path.isdir(path):
            return os.path.basename(path) == REPORT_DIR
        return False
    except:
        return False

def is_in_reports_dir(path):
    try:
        if path is None:
            return False

        cur_dir = path if os.path.isdir(path) else os.path.dirname(path)
        while True:
            parent_dir = os.path.dirname(cur_dir)
            if is_root_reports_dir(cur_dir):
                return True
            else:
                if cur_dir == parent_dir:
                    return False
                else:
                    cur_dir = parent_dir
    except:
        return False


# pre-condition: check if is_in_project_dir(path)
# return True if path is root tests dir
def is_root_tests_dir(path):
    try:
        if path is None:
            return False

        if os.path.isdir(path):
            return os.path.basename(path) == TESTS_DIR
        return False
    except:
        return False

def is_in_tests_dir(path):
    try:
        if path is None:
            return False

        cur_dir = path if os.path.isdir(path) else os.path.dirname(path)
        while True:
            parent_dir = os.path.dirname(cur_dir)
            if is_root_tests_dir(cur_dir):
                return True
            else:
                if cur_dir == parent_dir:
                    return False
                else:
                    cur_dir = parent_dir
    except:
        return False

# pre-condition: check if is_in_project_dir(path)
# return True if path is dir in root tests dir
# with_check=True means it returns True only for valid testcase dirs (with 'dotest.sh' file in it)
def is_testcase_dir(path, with_check=True):
    try:
        if path is None:
            return False

        if os.path.isdir(path):
            parent_dir = os.path.dirname(path)
            if is_root_tests_dir(parent_dir):
                if with_check:
                    file_list = os.listdir(path)
                    if TEST_FILE in file_list:
                        return True
                else:
                    return True
        return False    
    except:
        return False


def is_testcase_result_dir(solution_id, path):
    try:
        if path is None or solution_id is None:
            return False

        if is_in_solution_dir(solution_id, path) and os.path.isdir(path):
            return os.path.basename(os.path.dirname(path)) == RESULTS_SUB_DIR
    except:
        return False

########################## GET DIRS/FILES ##########################

# dst: regex for match
# src: dir path which is tested to regex
def match_regex(dst_regex, src_path):
    return bool(re.match(dst_regex, src_path))


# try match regex on dir parents
# returns parent dir name which matches regex or None
# ex: "x[a-z]{5}[0-9]{2}", "subj1/projA/xlogin00/test1/file" --> "subj1/projA/xlogin00"
def get_parent_regex_match(reg, dir_path):
    if dir_path is None:
        return None
    try:
        cur_dir = dir_path
        while True:
            parent_dir = os.path.dirname(cur_dir)
            if match_regex(reg, os.path.basename(cur_dir)):
                return cur_dir
            else:
                if cur_dir == parent_dir:
                    return None
                else:
                    cur_dir = parent_dir
    except Exception as err:
        log("get parent regex match | "+str(err)+" | "+str(traceback.format_exc()))
        return None


"""
proj_path = get_proj_path(path)
if proj_path is not None:
    proj_data = load_proj_from_conf_file(proj_path)

    # create Project obj from proj data
    proj = Project(proj_path)
    proj.set_values_from_conf(proj_data)
"""

# return path to proj conf file if given path is in proj dir
def get_proj_path(path):
    try:
        if path is None:
            return None

        cur_dir = path if os.path.isdir(path) else os.path.dirname(path)
        while True:
            parent_dir = os.path.dirname(cur_dir)
            if is_root_project_dir(cur_dir):
                return cur_dir
            else:
                if cur_dir == parent_dir:
                    return None
                else:
                    cur_dir = parent_dir
    except Exception as err:
        log("get proj path | "+str(err))
        return None


# pre-condition: check if is_in_project_dir(path)
# return path to root solution dir if given path is in some solution dir
# ex: "x[a-z]{5}[0-9]{2}", "subj1/projA/xlogin00/test1/file" --> "subj1/projA/xlogin00"
def get_root_solution_dir(solution_id, path):
    # return get_parent_regex_match(solution_id, path)
    try:
        if path is None or solution_id is None:
            return None

        cur_dir = path if os.path.isdir(path) else os.path.dirname(path)
        while True:
            parent_dir = os.path.dirname(cur_dir)
            if is_root_solution_dir(solution_id, cur_dir):
                return cur_dir
            else:
                if cur_dir == parent_dir:
                    return None
                else:
                    cur_dir = parent_dir
    except Exception as err:
        log("get root solution dir | "+str(err))
        return None


def get_root_tests_dir(path):
    try:
        if path is None:
            return None

        cur_dir = path if os.path.isdir(path) else os.path.dirname(path)
        while True:
            parent_dir = os.path.dirname(cur_dir)
            if is_root_tests_dir(cur_dir):
                return cur_dir
            else:
                if cur_dir == parent_dir:
                    return None
                else:
                    cur_dir = parent_dir
    except Exception as err:
        log("get root tests dir | "+str(err))
        return None


def get_root_testcase_dir(path):
    try:
        if path is None:
            return None

        cur_dir = path if os.path.isdir(path) else os.path.dirname(path)
        while True:
            parent_dir = os.path.dirname(cur_dir)
            if is_testcase_dir(cur_dir):
                return cur_dir
            else:
                if cur_dir == parent_dir:
                    return None
                else:
                    cur_dir = parent_dir
    except Exception as err:
        log("get root testcase dir | "+str(err))
        return None


# return list of solution dirs in current project directory (cwd)
def get_solution_dirs(env):
    result = set()
    if env.cwd.proj is not None:
        solution_id = env.cwd.proj.solution_id
        items = os.listdir(env.cwd.proj.path) # list all dirs and files in proj dir
        for item in items:
            path = os.path.join(env.cwd.proj.path, item)
            if is_root_solution_dir(solution_id, path):
                result.add(path)
    else:
        log("get_solution_dirs | cwd is not project root directory")
    return list(result)


# return list of solution files in current project directory (cwd)
def get_solution_files(env):
    result = set()
    if env.cwd.proj is not None:
        solution_id = env.cwd.proj.solution_id
        items = os.listdir(env.cwd.proj.path) # list all dirs and files in proj dir
        for item in items:
            path = os.path.join(env.cwd.proj.path, item) # path ex: subj1/projA/xlogin00.*
            if is_solution_file(solution_id, path):
                result.add(path)
    else:
        log("get_solution_files | cwd is not project root directory")
    return list(result)


# return list of solution archive dirs in current directory (cwd) if its project directory
# solution_archives = list of *paths* to valid solution archives
# solution_files = list of *file names* to some solution files
def get_solution_archives(env):
    solution_archives = set() # zipfile or tarfile
    solution_files = set() # other solution matched file
    for file_name in get_solution_files(env):
        if is_archive_file(file_name):
            solution_archives.add(file_name)
        else:
            log("solution file but not zipfile or tarfile: "+str(os.path.basename(file_name)))
            solution_files.add(os.path.basename(file_name))
    # log(str(solution_archives))
    # log(str(solution_files))
    return list(solution_archives), list(solution_files)


# return list of test dirs (dirs from project_dir/tests_dir/*)
# with_check=True means it returns only valid test dirs (with 'dotest.sh' file in it)
def get_valid_tests_names(env):
    result_names = set()
    if env.cwd.proj is not None:
        tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
        items = os.listdir(tests_dir) # list all dirs and files in tests dir
        for item in items:
            path = os.path.join(tests_dir, item)
            if is_testcase_dir(path, with_check=True):
                result_names.add(item)
    else:
        log("get_solution_dirs | cwd is not project root directory")
    return list(result_names)
