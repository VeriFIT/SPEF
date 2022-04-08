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



def create_test_suite(testsuite_file):
    if not os.path.exists(testsuite_file):
        with open(testsuite_file, 'w+') as f:
            f.write("#!/usr/bin/env bash\n")
            f.write("# ***** write test strategy here *****\n")


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

        # create tests dir if not exists
        tests_dir = os.path.join(proj_dir, TESTS_DIR)
        scoring_file = os.path.join(tests_dir, SCORING_FILE)
        testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)
        if not os.path.exists(tests_dir):
            os.mkdir(tests_dir)
            with open(scoring_file, 'w+'): pass # create scoring file
            create_test_suite(testsuite_file) # create testsuite file


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

        # create file for test script (dotest.sh)
        with open(os.path.join(new_test_dir, TEST_FILE), 'w+') as f:
            f.write("#!/bin/bash\n")
            f.write("# ***** write test here *****\n")
            f.write("# press Fx to see all available functions and variables you can use")

        # set default scoring for new test
        with open(scoring_file, 'a+') as f:
            f.write(f"{test_name}_ok=1; {test_name}_fail=0\n")

        log("create new test | scoring set to default (ok=1, fail=0) -- you can change it in: "+str(scoring_file))

        return new_test_dir
    except Exception as err:
        log("create new test | "+str(err)+" | "+str(traceback.format_exc()))
        return None
