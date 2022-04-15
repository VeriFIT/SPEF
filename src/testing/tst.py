#!/usr/bin/env python3

import os
import shutil
import stat
import subprocess

from pathlib import Path


from utils.logger import *
from utils.loading import *
from utils.parsing import parse_sum_equation

from modules.bash import Bash_action

# SRC_BASH_FILE = 'testing/tst_orig.sh"
# DST_BASH_FILE = 'src/tst"
# bash_file = os.path.join(tests_dir, DST_BASH_FILE)

# funkcie pre testsuite.sh a dotest.sh su v "tests/src/tst" (tst run, tst sum, tst clean,...)


IMAGE_NAME = 'test'
RUN_FILE = 'run.sh'

SHARED_DIR = os.path.join(HOME, 'docker_shared')
SHARED_TESTS_DIR = os.path.join(SHARED_DIR, 'tests')
SHARED_RESULTS_DIR = os.path.join(SHARED_DIR, 'results')
SHARED_SUT_DIR = os.path.join(SHARED_DIR, 'sut')
SHARED_RUN_FILE = os.path.join(SHARED_TESTS_DIR, RUN_FILE)

CONTAINER_DIR = '/opt'
CONTAINER_TESTS_DIR = os.path.join(CONTAINER_DIR, 'tests')
CONTAINER_RESULTS_DIR = os.path.join(CONTAINER_DIR, 'results')
CONTAINER_SUT_DIR = os.path.join(CONTAINER_DIR, 'sut')
CONTAINER_RUN_FILE = os.path.join(CONTAINER_TESTS_DIR, RUN_FILE)


SRC_BASH_FILE = os.path.join(HOME, 'testing', 'tst_orig.sh')


# ocakavam ze je vytvoreny image s menom `test`
# tests_dir a solution_dir su absolutne cesty src tests a src xlogin

def run_testsuite_in_docker(env, solution_dir):
    if not env.cwd.proj or not solution_dir:
        log("run testsuite in docker | run from solution dir in some project dir")
        return env

    # ci su nakopirovane bash funkcie v tests_dir (ak nie, nakopiruj ich do tests_dir/DST_BASH_FILE)
    bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)
    if not bash_tests_ok:
        log("run testsuite | problem with bash functions for tests")
        return env


    # prepare shared dir and subdirs for testing data
    if not os.path.exists(SHARED_DIR): os.mkdir(SHARED_DIR)
    if not os.path.exists(SHARED_RESULTS_DIR): os.mkdir(SHARED_RESULTS_DIR)


    # copy data for testing to shared dir
    tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
    file_to_run = os.path.join(HOME, 'testing', 'run_testsuite.sh')
    shutil.copytree(tests_dir, SHARED_TESTS_DIR)
    shutil.copytree(solution_dir, SHARED_SUT_DIR)
    shutil.copyfile(file_to_run, SHARED_RUN_FILE)


    # get user id
    USER = os.getenv('USER')
    is_root = False
    if USER =='root':
        is_root = True
    output = subprocess.run(f"id -u {USER}".split(' '), capture_output=True)
    user_id = output.stdout.decode('utf-8').strip()

    # create container from image `test`
    container_cid_file = '/tmp/docker.cid'

    out = subprocess.run(f"docker run --cidfile {container_cid_file} --rm -d --workdir {CONTAINER_DIR} -v {SHARED_DIR}:{CONTAINER_DIR}:z {IMAGE_NAME} bash -c".split(' ')+["while true; do sleep 1; done"],  capture_output=True)
    # return env
    with open(container_cid_file, 'r') as f:
        cid = f.read()
    if not is_root:
        output = subprocess.run(f"docker exec {cid} useradd -u {user_id} test".split(' '), capture_output=True)

    """
    cd sut
    /opt/tests/run.sh
    """
    # run test script
    output = subprocess.run(f"docker exec --user {user_id} --workdir {CONTAINER_SUT_DIR} {cid} bash {CONTAINER_RUN_FILE}".split(' '), capture_output=True)
    result = output.stdout.decode('utf-8')
    err = output.stderr.decode('utf-8')

    # log("---------- res ----------")
    # log(result)
    # log(err)
    # TODO: vypisat stdout a stderr

    # remove container
    out = subprocess.run(f"docker rm -f {cid}".split(' '), capture_output=True)

    # get results from test script
    # with open(os.path.join(shared_results_dir, ... ), 'r') as f:
    #    data = f.read()




    # sudo rm -rf docker_shared/
    # sudo rm /tmp/docker.cid
    # docker rm -f {cid}

    # clear temporary files and dirs
    try:
        os.remove(container_cid_file)
        shutil.rmtree(SHARED_DIR)
    except Exception as err:
        log("remove | "+str(err))
        pass


    return env





def calculate_score(env, solution_dir):
    try:
        if not env.cwd.proj or not solution_dir:
            return None

        total_score = None

        # load sum file
        tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
        sum_file = os.path.join(tests_dir, SUM_FILE)
        sum_equation_str = load_sum_equation_from_file(env, sum_file)

        # parse sum equation
        equation, ignored_tags = parse_sum_equation(env, solution_dir, sum_equation_str)
        equation = ' '.join(str(x) for x in equation)

        # calculate sum
        if equation != '':
            result = eval(equation)
            log(result)
            return result
        else:
            log("calculate score sum | no tag from SUM equation was found")
            log("ignored tags: "+str(ignored_tags))
            return None

        return total_score
    except Exception as err:
        log("calculate score sum | "+str(err))
        return None


def check_bash_functions_for_testing(proj_dir):
    tests_dir = os.path.join(proj_dir, TESTS_DIR)
    bash_file = os.path.join(tests_dir, DST_BASH_FILE)
    bash_file_exists = False
    if os.path.exists(bash_file):
        bash_file_exists = True
    else:
        try:
            if os.path.exists(SRC_BASH_FILE):
                shutil.copyfile(SRC_BASH_FILE, bash_file)
                st = os.stat(bash_file)
                os.chmod(bash_file, st.st_mode | stat.S_IEXEC)
                bash_file_exists = True
        except Exception as err:
            log("copy bash functions | "+str(err))
    return bash_file_exists



# bin/t
""" /bin/t --> spusti /tests/testsuite.sh --- ten spusta /bin/tst run param """
def run_testsuite(env, solution_dir):
    try:
        if not env.cwd.proj or not solution_dir:
            log("run testsuite | run from solution dir in some project dir")
            return env

        ############### 1. nastavenie premennych ###############
        command = ""
        proj_dir = env.cwd.proj.path
        tests_dir = os.path.join(proj_dir, TESTS_DIR)
        scoring_file = os.path.join(tests_dir, SCORING_FILE)
        testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)
        if not os.path.exists(tests_dir) or not os.path.isdir(tests_dir):
            log(f"run testsuite | tests_dir '{tests_dir}' doesnt exists or its not a directory")
            return env
        if not os.path.exists(scoring_file):
            log(f"run testsuite | scoring file '{scoring_file}' doesnt exist")
            return env
        if not os.access(testsuite_file, os.X_OK):
            log(f"run testsuite | scoring file '{testsuite_file}' is not executable (try: chmod +x testsuite.sh)")
            return env
        if not os.path.exists(testsuite_file):
            log(f"run testsuite | testsuite '{testsuite_file}' doesnt exist")
            return env
        if not os.access(testsuite_file, os.X_OK):
            log(f"run testsuite | testsuite '{testsuite_file}' is not executable (try: chmod +x testsuite.sh)")
            return env


        """
        # if [ -f $PROJDIR/sandbox.config ]; then
            # . $PROJDIR/sandbox.config
        # fi
        # export SANDBOXUSER
        # export SANDBOXDIR
        # export SANDBOXLOCK
        """
        ############### 2. nastavenie izolovaneho prostredia ###############
        # TODO !!!!!!!
        pass


        ############### 3. kontrola bash funkcii v tests_dir ###############
        # ci su nakopirovane bash funkcie v tests_dir (ak nie, nakopiruj ich do tests_dir/DST_BASH_FILE)
        bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)
        if not bash_tests_ok:
            log("run testsuite | problem with bash functions for tests")
            return env


        ############### 4. spristupni tst funkcie ###############
        # spristupnit bin/tst (run_test), bin/n (add_note) pre testsuite.sh
        # TODO !!!!!!!
        # SRC_BASH_DIR = '/testing/tst.py'  --> SRC_BASH_DIR/tst.py run test_name
        # SRC_BASH_DIR = '/testing/tst'     --> SRC_BASH_DIR/tst run test_name
        # command += f"export PATH={SRC_BASH_DIR}:$PATH\n"  
        bash_dir = os.path.join(tests_dir, DST_BASH_DIR)
        login = os.path.basename(solution_dir)
        command += f"export PATH={bash_dir}:$PATH\n"
        command += f"export TESTSDIR={tests_dir}\n"
        command += f"export TEST_FILE={TEST_FILE}\n"
        command += f"export login={login}\n"
        # command += f"export SCORING={scoring_file}\n"


        ############### 5. spusti testsuite ###############
        # (execute sh script)
        command += f"cd {solution_dir}\n"
        command += f"{testsuite_file}\n"

        # command += f"{print_score}\n"

        env.bash_active = True
        env.bash_action = Bash_action()
        env.bash_action.dont_jump_to_cwd()
        env.bash_action.add_command(command)
        return env

        # PRINT SCORE
        # echo ====================================
        # grep -m1 "^[0-9].*:celkem" hodnoceni-auto
        # echo Stiskni enter...; read
    except Exception as err:
        log("run testsuite | "+str(err))
        return env



# bin/tst
""" /bin/tst run param --> spusti /tests/tst run param"""
def run_tests(env, solution_dir, test_list):
    try:
        if test_list == []: # no test to run
            return env

        if not env.cwd.proj or not solution_dir:
            log("run test | run from solution dir in some project dir")
            return

        ############### 1. nastavenie premennych ###############
        command = ""
        tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
        if not os.path.exists(tests_dir) or not os.path.isdir(tests_dir):
            log(f"run test | tests_dir '{tests_dir}' doesnt exists or its not a directory")
            return env
        for test_name in test_list:
            test_dir = os.path.join(tests_dir, test_name)
            if not is_testcase_dir(test_dir, with_check=True):
                log(f"run test | '{test_dir}' is not valid test dir with dotest.sh in it")
                return env


        """
        # if [ -f $PROJDIR/sandbox.config ]; then
            # . $PROJDIR/sandbox.config
        # fi
        # export SANDBOXUSER
        # export SANDBOXDIR
        # export SANDBOXLOCK
        """
        ############### 2. nastavenie izolovaneho prostredia ###############
        # TODO !!!!!!!
        pass


        ############### 3. kontrola bash funkcii v tests_dir ###############
        # ci su nakopirovane bash funkcie v tests_dir (ak nie, nakopiruj ich do tests_dir/DST_BASH_FILE)
        bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)
        if not bash_tests_ok:
            log("run test | problem with bash functions for tests")
            return env


        ############### 4. spusti test ###############
        tst_file = os.path.join(tests_dir, DST_BASH_FILE)
        login = os.path.basename(solution_dir)
        command += f"export TESTSDIR={tests_dir}\n"
        command += f"export TEST_FILE={TEST_FILE}\n"
        command += f"export login={login}\n"
        command += f"cd {solution_dir}\n"
        for test_name in test_list:
            command += f"{tst_file} run {test_name};"
        command += "\n"

        # command += f"{print_score}\n"

        env.bash_active = True
        env.bash_action = Bash_action()
        env.bash_action.dont_jump_to_cwd()
        env.bash_action.add_command(command)
        return env
    except Exception as err:
        log("run test | "+str(err))
        return env


# bin/c
def clean_test():
    pass

# bin/s
def get_sum():
    pass




# bin/n
""" /bin/n --> nacita /tests/scoring + spusti /tests/tst sum"""
def add_note(stdscr, env):
    pass
    # from testing import tst
    # tst_sum()


# bin/p
def make_patch():
    pass


