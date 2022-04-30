import os
import re
import glob
import shutil
import traceback
import tarfile
import zipfile

from utils.loading import *
from utils.logger import *
from utils.match import *
from utils.reporting import *
from utils.history import history_test_event

from testing.tst import check_bash_functions_for_testing
from testing.report import copy_default_report_template


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


def rename_solutions(proj, solution=None):
    required_name = proj.sut_required
    extended_variants = proj.sut_ext_variants
    ok, renamed, fail = [], [], []
    if solution is not None:
        solutions = [solution]
    else:
        solutions = [data for key, data in proj.solutions.items()]
    for solution in solutions:
        try:
            solution_dir = solution.path
            # find sut in solution dir
            file_list = glob.glob(os.path.join(solution_dir, '**', required_name), recursive=True)
            file_list = filter_intern_files(file_list)
            if len(file_list) == 1: # only one file matches the sut required
                ok.append(os.path.basename(solution_dir))
            else:
                files = []
                for ext in extended_variants: # find extended version of sut in solution dir
                    files.extend(glob.glob(os.path.join(solution_dir, '**', ext), recursive=True))
                files = filter_intern_files(files)
                if len(files) == 1: # only one file matches some sut extened variant
                    old_file = files[0]
                    new_file = os.path.join(os.path.dirname(old_file), required_name)
                    shutil.copy(old_file, new_file)
                    renamed.append(os.path.basename(solution_dir))
                    solution.tags.set_tag("renamed_sut", [f"{os.path.basename(old_file)}-->{os.path.basename(new_file)}"])
                    save_tags_to_file(solution.tags)
                else:
                    fail.append(os.path.basename(solution_dir))
        except:
            fail.append(os.path.basename(solution_dir))
    return ok, renamed, fail


""" vola sa ked sa otvori subor z test_dir na edit """
# create copy of test dir -> tmp/test/v/*
# return success
def copy_test_history_to_tmp(proj_dir, test_dir):
    try:
        # check if history dir exists
        history_dir = os.path.join(proj_dir, HISTORY_DIR)
        if not os.path.exists(history_dir) or not os.path.isdir(history_dir):
            create_tests_history_dir(history_dir)

        testcase_tags = load_testcase_tags(test_dir)
        if testcase_tags is not None:
            # get version of test
            args = testcase_tags.get_args_for_tag("version")
            version = 1 if args is None or len(args) < 1 else int(args[0])

            # create tmp dir for test with actual version
            test_name = os.path.basename(test_dir)
            tmp_test_dir = os.path.join(TMP_DIR, test_name)
            tmp_test_v_dir = os.path.join(tmp_test_dir, f"version_{version}")
            if not os.path.exists(tmp_test_dir):
                os.mkdir(tmp_test_dir)
            if os.path.exists(tmp_test_v_dir):
                log(f"copy test dir to history | tmp file for test {test_name} and version {version} already exists!!")
                return False
            else:
                # copy test dir to tmp dir
                shutil.copytree(test_dir, tmp_test_v_dir)
                log("test history saved to tmp dir")
            return True
        else:
            log("copy test dir to history | cannot find test tags")
            return False
    except Exception as err:
        log("copy test dir to history | "+str(err)+" | "+str(traceback.format_exc()))
        return False



""" vola sa pri save buffer ak sa edituje test dir """
def actualize_test_history_in_tmp(proj_dir, test_dir):
    # check if history dir exists
    history_dir = os.path.join(proj_dir, HISTORY_DIR)
    if not os.path.exists(history_dir) or not os.path.isdir(history_dir):
        create_tests_history_dir(history_dir)

    testcase_tags = load_testcase_tags(test_dir)
    if testcase_tags is not None:
        # get version of test
        args = testcase_tags.get_args_for_tag("version")
        version = 1 if args is None or len(args) < 1 else int(args[0])

        # create tmp dir for test with actual version
        test_name = os.path.basename(test_dir)
        tmp_test_dir = os.path.join(TMP_DIR, test_name)
        tmp_test_v_dir = os.path.join(tmp_test_dir, f"version_{version}")
        if not os.path.exists(tmp_test_dir):
            os.mkdir(tmp_test_dir)
        # copy test dir to tmp dir
        shutil.copytree(test_dir, tmp_test_v_dir, dirs_exist_ok=True)


def create_project(env):
    # create project object
    proj = Project(env.cwd.path)
    proj.set_default_values()
    proj_data = proj.to_dict()
    save_proj_to_conf_file(proj.path, proj_data)
    env.cwd.proj = proj

    # create report dir
    report_dir = os.path.join(proj.path, REPORT_DIR)
    create_report_dir(report_dir)

    # create tests dir
    tests_dir = os.path.join(proj.path, TESTS_DIR)
    create_tests_dir(tests_dir)

    # create history dir
    history_dir = os.path.join(proj.path, HISTORY_DIR)
    create_tests_history_dir(history_dir)
    return env


############ REPORT ############
def create_report_dir(report_dir):
    report_template = os.path.join(report_dir, REPORT_TEMPLATE)
    if not (os.path.exists(report_dir) and os.path.isdir(report_dir)):
        os.mkdir(report_dir)
    if not os.path.exists(report_template):
        copy_default_report_template(report_template)


############ HISTORY ############
def create_tests_history_dir(history_dir):
    testsuite_history = os.path.join(history_dir, HISTORY_FILE)
    if not (os.path.exists(history_dir) and os.path.isdir(history_dir)):
        os.mkdir(history_dir)
    if not os.path.exists(testsuite_history):
        with open(testsuite_history, 'w+'): pass


############ TESTS ############
# create tests dir with necessary files
def create_tests_dir(tests_dir):
    testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)
    scoring_file = os.path.join(tests_dir, SCORING_FILE)
    sum_file = os.path.join(tests_dir, SUM_FILE)
    testsuite_tags = os.path.join(tests_dir, TESTSUITE_TAGS)

    if not (os.path.exists(tests_dir) and os.path.isdir(tests_dir)):
        os.mkdir(tests_dir)
    create_scoring_file(scoring_file) # create scoring file
    create_sum_file(sum_file) # create sum file
    create_testsuite(testsuite_file) # create testsuite file
    create_testsuite_tags_file(testsuite_tags) # create file for testsuite tags 


############ SUM ############
def create_sum_file(sum_file):
    mess = """# POZOR:
#   * mozno pouzivat len tagy s prefixom 'scoring_'
#       - prefix sa pri parsovani rovnice pre vypocet SUM prida automaticky
#       - ak teda existuje tag 'scoring_test_x', v rovnici ho pouzi ako 'test_x'
#   * mozno pouzivat len tagy ktore maju presne jeden parameter
#       - tag s viacerymi parametrami --> do rovnice sa berie hodnota prveho parametra
#       - tag bez parametra --> v rovnici sa ignoruje (a vypise sa upozornenie)
#       - tag, ktory neexistuje --> v rovnici sa ignoruje (a vypise sa upozornenie)
#   * v rovnici mozno pouzit len znamienka: + - *
#   * zatvorky nie su podporovane
#       - pre zlozitejsie vypocty je potreba vytvorit extra tag pre medzivypocet
#       - napr. vytvorim manualne tag 'scoring_medzihodnota(body)' ktory sa pouzije v SUM ako 'medzihodnota'
#   * okrem tagov mozno pouzit specialnu funkciu SUM_ALL_TESTS
#       - tato funkcia scita hodnoty tagov z platnych testov
#       - moze sa pouzit v kombinacii s dalsimi tagmi
#       - napr: SUM=SUM_ALL_TESTS + documentation - renamed_solution
"""
    if not os.path.exists(sum_file):
        with open(sum_file, 'w+') as f:
            f.write(mess)
            f.write("SUM=SUM_ALL_TESTS\n")

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
        # copy bash functions to tests/src/tst file
        check_bash_functions_for_testing(proj_dir)

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
        history_test_event(proj_dir, test_name, "create new test")

        # set default scoring for new test
        scoring_file = os.path.join(tests_dir, SCORING_FILE)
        with open(scoring_file, 'a+') as f:
            f.write(f"{test_name}_ok=1; {test_name}_fail=0\n")

        log("create new test | scoring set to default (ok=1, fail=0) -- you can change it in: "+str(scoring_file))

        return new_test_dir
    except Exception as err:
        log("create new test | "+str(err)+" | "+str(traceback.format_exc()))
        return None
