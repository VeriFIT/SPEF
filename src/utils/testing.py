

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


# TODO: export FUT from env.cwd.proj.sut_expected (nie z scoring)
# TODO: copy solution_dir do /opt/sut vsetko okrem 'solution_tags.yaml'
# TODO: copy solution_dir do /opt/sut predtym spravt tst clear

# TODO: solution/testxx/ adresare by sa mali ukladat vsetky do solution/tests/testxx/
# TODO: tests_tags.yaml sa vytvori v precinku s testsuite.sh a nie v solution_dir

# TODO: automaticka suma tagov
# TODO: automaticky report tagov

CONTAINER_DIR = '/opt'
CONTAINER_TESTS_DIR = '/opt/tests'
CONTAINER_SUT_DIR = '/opt/sut/'
CONTAINER_RUN_FILE = '/opt/tests/run.sh'

SHARED_DIR = os.path.join(TMP_DIR, 'docker_shared')
SHARED_TESTS_DIR = os.path.join(TMP_DIR, 'docker_shared/tests')
SHARED_SUT_DIR = os.path.join(TMP_DIR, 'docker_shared/sut')
SHARED_RUN_FILE = os.path.join(TMP_DIR, 'docker_shared/tests/run.sh')

# shell functions
TST_FCE_DIR = 'src'
TST_FCE_FILE = 'src/tst' # proj/tests/src/tst
SRC_BASH_FILE = os.path.join(HOME, 'testing', 'bash' 'tst.sh')
SRC_RUN_FILE = os.path.join(HOME, 'testing', 'bash', 'run_testsuite.sh')

# TODO: SRC_BASH_FILE rozdelit na dva subory: podpora pre "dotest.sh" a funkcie pre "testsuite.sh"
# funkcie pre "testsuite.sh" a "dotest.sh" su v "tests/src/tst" (tst run, tst sum, tst clean,...)



# export FUT={fut}\n\

def get_cmd_run_testsuite(tst_fce_dir, tests_dir, sut_dir_name, fut):
    cmd = f"""\
export PATH={tst_fce_dir}:$PATH\n\
export TESTSDIR={tests_dir}\n\
export TEST_FILE={TEST_FILE}\n\
export LOGIN={sut_dir_name}\n\
export SCORING={SCORING_FILE}
export TAG_FILE={TESTS_TAGS}
{tests_dir}/{TESTSUITE_FILE}\n\
"""
    return cmd



# ocakavam ze je vytvoreny image s menom `test`
# tests_dir a solution_dir su absolutne cesty src tests a src xlogin

def run_testsuite_in_docker(env, solution_dir):
    if not env.cwd.proj or not solution_dir:
        log("run testsuite in docker | run from solution dir in some project dir")
        return env

    # check if tst fce file is in proj/tests/src/ dir
    bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)
    if not bash_tests_ok:
        log("run testsuite | problem with bash functions for tests")
        return env


    # copy data for testing to shared dir
    tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
    os.makedirs('docker_shared', exist_ok=True)
    shutil.copytree(tests_dir, SHARED_TESTS_DIR) # proj/tests/ -> /docker_shared/tests/
    shutil.copytree(solution_dir, SHARED_SUT_DIR) # proj/xlogin/ -> /docker_shared/sut/
    shutil.copyfile(SRC_RUN_FILE, SHARED_RUN_FILE)

    # get user id
    USER = os.getenv('USER')
    is_root = False
    if USER =='root':
        is_root = True
    output = subprocess.run(f"id -u {USER}".split(' '), capture_output=True)
    user_id = output.stdout.decode('utf-8').strip()

    # create container from image `test` (IMAGE_NAME)
    container_cid_file = '/tmp/docker.cid'
    out = subprocess.run(f"docker run --cidfile {container_cid_file} --rm -d --workdir {CONTAINER_DIR} -v {SHARED_DIR}:{CONTAINER_DIR}:z {IMAGE_NAME} bash -c".split(' ')+["while true; do sleep 1; done"],  capture_output=True)
    with open(container_cid_file, 'r') as f:
        cid = f.read()
    if not is_root:
        output = subprocess.run(f"docker exec {cid} useradd -u {user_id} test".split(' '), capture_output=True)

    # run test script (cd sut; /opt/tests/run.sh)
    output = subprocess.run(f"docker exec --user {user_id} --workdir {CONTAINER_SUT_DIR} {cid} bash {CONTAINER_RUN_FILE}".split(' '), capture_output=True)
    result = output.stdout.decode('utf-8')
    err = output.stderr.decode('utf-8')

    log(result)
    log(err)


    # remove container
    out = subprocess.run(f"docker rm -f {cid}".split(' '), capture_output=True)

    # get results from test script
    solution_results_dir = os.path.join(solution_dir, 'tests')
    shutil.copytree(SHARED_SUT_DIR, solution_results_dir)

    # with open(os.path.join(SHARED_SUT_DIR, ... ), 'r') as f:
    #    data = f.read()



    # sudo rm -rf docker_shared/
    # sudo rm /tmp/docker.cid
    # docker rm -f {cid}

    # clear temporary files and dirs
    try:
        os.remove(container_cid_file)
        shutil.rmtree(SHARED_DIR)
    except Exception as err:
        log("remove shared dir | "+str(err))
        pass

    return env




def calculate_score(env, solution_dir):
    try:
        if not env.cwd.proj or not solution_dir:
            return None

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
            return result
        else:
            log("calculate score sum | no tag from SUM equation was found")
            log("ignored tags: "+str(ignored_tags))
            return None

    except Exception as err:
        log("calculate score sum | "+str(err))
        return None


def check_bash_functions_for_testing(proj_dir):
    bash_file = os.path.join(proj_dir, TST_FCE_FILE)
    bash_file_exists = False
    if os.path.exists(bash_file):
        bash_file_exists = True
        log("file with bash functions exists")
    else:
        log("file with bash functions not exists")
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
        tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
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


        ############### 2. kontrola bash funkcii v tests_dir ###############
        # ci su nakopirovane bash funkcie v tests_dir (ak nie, nakopiruj ich do tests_dir/DST_BASH_FILE)
        bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)
        if not bash_tests_ok:
            log("run testsuite | problem with bash functions for tests")
            return env


        ############### 3. spusti testsuite ###############
        # spristupnit bin/tst (run_test), bin/n (add_note) pre testsuite.sh
        # TODO !!!!!!!
        # SRC_BASH_DIR = '/testing/tst.py'  --> SRC_BASH_DIR/tst.py run test_name
        # SRC_BASH_DIR = '/testing/tst'     --> SRC_BASH_DIR/tst run test_name
        # command += f"export PATH={SRC_BASH_DIR}:$PATH\n"  
        bash_dir = os.path.join(tests_dir, TST_FCE_DIR)
        login = os.path.basename(solution_dir)
        command += f"export PATH={bash_dir}:$PATH\n"
        command += f"export TESTSDIR={tests_dir}\n"
        command += f"export TEST_FILE={TEST_FILE}\n"
        command += f"export TAG_FILE={TESTS_TAGS}\n"
        command += f"export login={login}\n"
        # command += f"export SCORING={scoring_file}\n"
        command += f"cd {solution_dir}\n"
        command += f"{testsuite_file}\n"

        # command += f"{print_score}\n"


        # ############### 3. spusti testsuite ###############
        # sut_dir_name = os.path.basename(solution_dir)
        # tst_fce_dir = os.path.join(tests_dir, TST_FCE_DIR)
        # fut = env.cwd.proj.sut_required
        # command = get_cmd_run_testsuite(tst_fce_dir, tests_dir, sut_dir_name, fut)
        # command += f"cd {solution_dir}\n"
        # command += f"{testsuite_file}\n"


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

        ############### 2. kontrola bash funkcii v tests_dir ###############
        # ci su nakopirovane bash funkcie v tests_dir (ak nie, nakopiruj ich do tests_dir/DST_BASH_FILE)
        bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)
        if not bash_tests_ok:
            log("run test | problem with bash functions for tests")
            return env


        ############### 3. spusti test ###############
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


