import os
import re
import glob
import shutil
import traceback
import tarfile
import zipfile

from utils.loading import *
from utils.printing import *
from utils.logger import *
from utils.match import *
from utils.reporting import *
from utils.history import history_new_test



def remove_archive_suffix(path):
    suffix_list = ['.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz', '.tar.xz', '.txz']
    for ext in suffix_list:
        path = path.removesuffix(ext)
    return path



# input: list of archive files
# output: set of problematic archives
def extract_archives(archives):
    problem_archives = set()
    for arch in archives:
        opener, mode = None, None
        if arch.endswith('.zip'):
            opener, mode = zipfile.ZipFile, 'r'
        elif arch.endswith('.tar'):
            opener, mode = tarfile.open, 'r'
        elif arch.endswith('.tar.gz') or arch.endswith('.tgz'):
            opener, mode = tarfile.open, 'r:gz'
        elif arch.endswith('.tar.bz2') or arch.endswith('.tbz'):
            opener, mode = tarfile.open, 'r:bz2'
        elif arch.endswith('.tar.xz') or arch.endswith('.txz'):
            opener, mode = tarfile.open, 'r:xz'
        else:
            problem_archives.add(os.path.basename(arch))

        try:
            if opener and mode:
                dest_dir = remove_archive_suffix(arch)
                with opener(arch, mode) as arch_file:
                    if not os.path.exists(dest_dir):
                        os.mkdir(dest_dir)
                    arch_file.extractall(dest_dir)
        except Exception as err:
            log("extract all from archive | "+str(err)+" | "+str(traceback.format_exc()))

    return problem_archives


def rename_solutions(src_dirs, required_name, extended_variants):
    ok, renamed, fail = [], [], []
    for solution in src_dirs:
        try:
            # find sut in solution dir
            file_list = glob.glob(os.path.join(solution, '**', required_name), recursive=True)
            file_list = filter_intern_files(file_list)
            if len(file_list) == 1: # only one file matches the sut required
                ok.append(solution)
            else:
                files = []
                for ext in extended_variants: # find extended version of sut in solution dir
                    files.extend(glob.glob(os.path.join(solution, '**', ext), recursive=True))
                files = filter_intern_files(files)
                if len(files) == 1: # only one file matches some sut extened variant
                    old_file = files[0]
                    new_file = os.path.join(os.path.dirname(old_file), required_name)
                    shutil.copy(old_file, new_file)
                    renamed.append(solution)
                    add_tag_to_solution(solution, "renamed_sut", [f"{os.path.basename(old_file)}-->{os.path.basename(new_file)}"])
                else:
                    fail.append(solution)
        except:
            fail.append(solution)
    return ok, renamed, fail



############ HISTORY ############
def create_tests_history_dir(history_dir):
    testsuite_history = os.path.join(history_dir, HISTORY_FILE)
    if not os.path.exists(history_dir):
        os.mkdir(history_dir)
        with open(testsuite_history, 'w+') as f: pass


############ TESTS ############
# create tests dir with necessary files
def create_tests_dir(tests_dir):
    testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)
    scoring_file = os.path.join(tests_dir, SCORING_FILE)
    sum_file = os.path.join(tests_dir, SUM_FILE)
    testsuite_tags = os.path.join(tests_dir, TESTSUITE_TAGS)
    if not os.path.exists(tests_dir):
        os.mkdir(tests_dir)
    create_scoring_file(scoring_file) # create scoring file
    create_sum_file(sum_file) # create sum file
    create_testsuite(testsuite_file) # create testsuite file
    create_testsuite_tags_file(testsuite_tags) # create file for testsuite tags 


############ SUM ############
def create_sum_file(sum_file):
    if not os.path.exists(sum_file):
        with open(sum_file, 'w+') as f:
            f.write("SUM=\n")


############ SCORING ############
def create_scoring_file(scoring_file):
    if not os.path.exists(scoring_file):
        with open(scoring_file, 'w+') as f:
            f.write("MAX_POINT=0\n")


############ TESTSUITE.SH ############
def create_testsuite(testsuite_file):
    if not os.path.exists(testsuite_file):
        with open(testsuite_file, 'w+') as f:
            f.write("#!/usr/bin/env bash\n")
            f.write("# ***** write test strategy here *****\n")


############ TESTSUITE_TAGS ############
def create_testsuite_tags_file(testsuite_tags):
    if not os.path.exists(testsuite_tags):
        with open(testsuite_tags, 'w+') as f: pass
        # add default tag for testsuite version
        version_tag = {"version": [1]}
        add_tag_to_file(testsuite_tags, version_tag)



# condition: path is root project dir (or path in proj dir)
# return path to new test dir if created succesfully (else return None)
def create_new_test(proj_dir, test_name=None):
    try:
        # try get path to root project dir
        if not is_root_project_dir(proj_dir):
            if is_in_project_dir:
                proj_dir = get_proj_path(proj_dir)
            else:
                log("create new test | must be in project (sub)dir")
                return None

        ############### TESTS ###############
        # create tests dir if not exists
        tests_dir = os.path.join(proj_dir, TESTS_DIR)
        create_tests_dir(tests_dir)

        ############### HISTORY ###############
        # create tests history dir if not exists
        history_dir = os.path.join(proj_dir, HISTORY_DIR)
        if not os.path.exists(history_dir):
            create_tests_history_dir(history_dir)


        ############### TEST ###############
        # create subdir in tests dir for new test --> TODO: define "test_dir_base" and "i"
        file_list = os.listdir(tests_dir)
        if (not test_name) or (test_name in file_list):
            test_dir_base = "test_"
            i = 1

            test_name = f"{test_dir_base}{i}"
            while test_name in file_list:
                i += 1
                test_name = f"{test_dir_base}{i}"
        new_test_dir = os.path.join(tests_dir, test_name)
        os.mkdir(new_test_dir)

        ############ DOTEST.SH ############
        # create file for test script (dotest.sh)
        with open(os.path.join(new_test_dir, TEST_FILE), 'w+') as f:
            f.write("#!/bin/bash\n")
            f.write("# ***** write test here *****\n")
            f.write("# press Fx to see all available functions and variables you can use")

        ############ TEST_TAGS ############
        # create file for test tags
        test_tags = os.path.join(new_test_dir, TESTCASE_TAGS)
        with open(test_tags, 'w+') as f: pass
        # add default tag for testsuite version
        version_tag = {"version": [1]}
        add_tag_to_file(test_tags, version_tag)

        # add event about creating new test to testsuite history
        # history_new_test(proj_dir, test_name)

        # set default scoring for new test
        scoring_file = os.path.join(tests_dir, SCORING_FILE)
        with open(scoring_file, 'a+') as f:
            f.write(f"{test_name}_ok=1; {test_name}_fail=0\n")

        log("create new test | scoring set to default (ok=1, fail=0) -- you can change it in: "+str(scoring_file))

        return new_test_dir
    except Exception as err:
        log("create new test | "+str(err)+" | "+str(traceback.format_exc()))
        return None
