import os
import shutil

import traceback

from utils.logger import *

from utils.loading import load_testcase_tags, load_testsuite_tags, save_tags_to_file


def is_test_history_in_tmp(proj_dir, test_name):
    testcase_dir = os.path.join(proj_dir, TESTS_DIR, test_name)
    testcase_tags = load_testcase_tags(testcase_dir)
    if testcase_tags is not None:
        # get version of test
        args = testcase_tags.get_args_for_tag("version")
        version = 1 if args is None or len(args) < 1 else int(args[0])

        # check if tmp dir with test with actual version exists
        tmp_test_v_dir = os.path.join(TMP_DIR, test_name, f"version_{version}")
        return os.path.exists(tmp_test_v_dir) and os.path.isdir(tmp_test_v_dir)


def history_test_removed(proj_dir, test_name):
    try:
        history_dir = os.path.join(proj_dir, HISTORY_DIR)
        history_file = os.path.join(history_dir, HISTORY_FILE)

        testcase_dir = os.path.join(proj_dir, TESTS_DIR, test_name)
        testcase_tags = load_testcase_tags(testcase_dir)
        if testcase_tags is not None:
            # get version of test
            args = testcase_tags.get_args_for_tag("version")
            version = 1 if args is None or len(args) < 1 else int(args[0])

            # copy test dir to history
            history_test_dir = os.path.join(history_dir, test_name)
            history_test_v_dir = os.path.join(history_test_dir, f"version_{version}")
            if not os.path.exists(history_test_dir) or not os.path.isdir(history_test_dir):
                os.mkdir(history_test_dir)
            if not os.path.exists(history_test_v_dir):
                # if actual version of this test do not already exists in history
                shutil.copytree(testcase_dir, history_test_v_dir)

            # add event to history logs
            history_test_event(proj_dir, test_name, f"remove test (version {version})")
            return True
    except Exception as err:
        log("history test removed | "+str(err)+" | "+str(traceback.format_exc()))
    return False


""" vola sa pri ukladani bufferu (ukladanie modifikovaneho testu) """
# increment test tag
# copy test from tmp dir to history dir
# increment testsuite tag
# add event to history logs
# return success
def history_test_modified(proj_dir, test_name):
    try:
        history_dir = os.path.join(proj_dir, HISTORY_DIR)
        history_file = os.path.join(history_dir, HISTORY_FILE)

        tests_dir = os.path.join(proj_dir, TESTS_DIR)
        testcase_dir = os.path.join(tests_dir, test_name)
        testcase_tags = load_testcase_tags(testcase_dir)
        if testcase_tags is not None:
            # get version of test
            args = testcase_tags.get_args_for_tag("version")
            if args is None or len(args) < 1:
                log("history test modified | test tags - cant find tag #version(int)")
                version = 1
            else:
                version = int(args[0])

            # check if tmp dir with test with actual version exists
            tmp_test_dir = os.path.join(TMP_DIR, test_name)
            tmp_test_v_dir = os.path.join(tmp_test_dir, f"version_{version}")
            if not os.path.exists(tmp_test_v_dir) or not os.path.isdir(tmp_test_v_dir):
                log("history test modified | test is not saved in tmp dir")
                return False

            # increment test version
            testcase_tags.set_tag('version', [str(version+1)])
            save_tags_to_file(testcase_tags)
            # add_tag_to_file(tags_file, {"version": [version+1]})
            # log("add tag to file: "+str(tags_file)+" version: "+str(version+1))

            # copy test from tmp dir to history
            history_test_dir = os.path.join(history_dir, test_name)
            history_test_v_dir = os.path.join(history_test_dir, f"version_{version}")
            if not os.path.exists(history_test_dir) or not os.path.isdir(history_test_dir):
                os.mkdir(history_test_dir)
            if os.path.exists(history_test_v_dir):
                log(f"history test modified | test {test_name} with version {version} already exists in history!!")
                return False
            shutil.copytree(tmp_test_v_dir, history_test_v_dir)

            # add event to history logs
            history_test_event(proj_dir, test_name, f"modify test (test version {version} -> {version+1})")

            # remove tmp dir with test
            # shutil.rmtree(tmp_test_v_dir)
            # log("remove tmp test dir")
        else:
            log("history test modified | cant load test tags ")
            return False
    except Exception as err:
        log("history test modified | "+str(err)+" | "+str(traceback.format_exc()))
        return False


# event = "create new test"
# event = "modify test"
# event = "delete test"
def history_test_event(proj_dir, test_name, event):
    if not event:
        return

    history_dir = os.path.join(proj_dir, HISTORY_DIR)
    history_file = os.path.join(history_dir, HISTORY_FILE)

    tests_dir = os.path.join(proj_dir, TESTS_DIR)
    testsuite_tags = load_testsuite_tags(tests_dir)
    if testsuite_tags is not None:
        # get testsuite version
        args = testsuite_tags.get_args_for_tag("version")
        if args is None or len(args) < 1:
            log("history new test | testsuite tags - cant find tag #version(int)")
            version = 1
        else:
            version = int(args[0])
            add_event_to_tests_history(history_file, version+1, test_name, event)
            testsuite_tags.set_tag('version', [str(version+1)])
            save_tags_to_file(testsuite_tags)
            # tags_file = os.path.join(tests_dir, TESTSUITE_TAGS)
            # add_tag_to_file(tags_file, {"version": [version+1]})
    else:
        log("history new test | cant load testsuite tags ")


def add_event_to_tests_history(file_path, version, test, event):
    with open(file_path, 'a+', encoding='utf8') as f:
        f.write(f"{version}:{test}:{event}\n")
