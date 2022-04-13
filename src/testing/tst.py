#!/usr/bin/env python3

import os
import shutil
import stat

from pathlib import Path


from utils.logger import *
from utils.loading import *

from modules.bash import Bash_action


SRC_BASH_DIR = os.path.join(Path(os.path.dirname(__file__)).parent,'testing')
SRC_BASH_FILE = os.path.join(SRC_BASH_DIR, 'tst_orig.sh')


# funkcie pre testsuite.sh a dotest.sh su v "tests/src/tst" (tst run, tst sum, tst clean,...)
DST_BASH_DIR = 'src'
DST_BASH_FILE = os.path.join(DST_BASH_DIR, 'tst')
# bash_file = os.path.join(tests_dir, DST_BASH_FILE)


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
def run_testsuite(stdscr, env, solution_dir):
    try:
        if not env.cwd.proj or not solution_dir:
            log("run testsuite | run from solution dir in some project dir")
            return

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
def run_test(stdscr, env, solution_dir, test_name):
    try:
        if not env.cwd.proj or not solution_dir:
            log("run test | run from solution dir in some project dir")
            return

        ############### 1. nastavenie premennych ###############
        command = ""
        tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
        test_dir = os.path.join(tests_dir, test_name)
        if not os.path.exists(tests_dir) or not os.path.isdir(tests_dir):
            log(f"run test | tests_dir '{tests_dir}' doesnt exists or its not a directory")
            return env
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
        command += f"{tst_file} run {test_name}\n"

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


