

#!/usr/bin/env python3

import os
import shutil
import stat
import subprocess
import datetime
import traceback

from pathlib import Path


from utils.logger import *
from utils.loading import *
from utils.parsing import parse_sum_equation
from utils.reporting import add_tag_to_solution

from modules.bash import Bash_action


# TODO: automaticky report (z tagov)
# TODO: n --> add note (vratane typical notes)



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
TST_FCE_FILE = 'tst' # proj/tests/src/tst
SRC_BASH_FILE = os.path.join(os.path.dirname(__file__), 'bash', 'tst.sh')
SRC_RUN_FILE = os.path.join(os.path.dirname(__file__), 'bash', 'run_testsuite.sh')


# TODO: SRC_BASH_FILE rozdelit na dva subory: podpora pre "dotest.sh" a funkcie pre "testsuite.sh"
# funkcie pre "testsuite.sh" a "dotest.sh" su v "tests/src/tst" (tst run, tst sum, tst clean,...)



def run_testsuite(env, solution_dir, show_results=True):
    try:
        if not env.cwd.proj or not solution_dir:
            log("run testsuite | run from solution dir in some project dir")
            return env

        ############### 1. CLEAN SOLUTION ###############
        clean_test(solution_dir)

        ############### 2. PREPARE DATA ###############
        data_ok = prepare_data(env, solution_dir)
        if not data_ok:
            log("run testsuite | problem with testing data")
            return env

        ############### 3. CHECK IF FUT EXISTS ###############
        fut = env.cwd.proj.sut_required
        file_list = os.listdir(solution_dir)
        if not fut in file_list:
            # add tag "missing sut file"
            log("run testsuite | fut file '{fut}' doesnt exists in solution dir")
            return env

        ############### 4. RUN TESTSUITE ###############
        succ = run_testsuite_in_docker(solution_dir, fut)
        if not succ:
            log("run testsuite | problem with testsuite run in docker")
            return env

        # get datetime and add tag "last_testing" to solution tags
        date_time = datetime.datetime.now().strftime("%d/%m/%y-%H:%M")
        add_tag_to_solution(solution_dir, "last_testing", [date_time])
        # get testsuite version and add tag "testsuite_version" to solution tags
        tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
        tests_tags = load_testsuite_tags(tests_dir)
        if tests_tags is not None and len(tests_tags)>0:
            version_args = tests_tags.get_args_for_tag("version")
            if version_args is not None:
                tst_version = list(version_args)[0]
                add_tag_to_solution(solution_dir, "testsuite_version", [tst_version])


        ############### 5. CALCULATE SCORE ###############
        total_score = calculate_score(env, solution_dir)
        # if found some tags from sum equation
        if total_score is not None:
            # add tag "score(body)" to solution
            score, bonus = total_score
            add_tag_to_solution(solution_dir, "score", [score])
            if bonus > 0:
                add_tag_to_solution(solution_dir, "score_bonus", [bonus])


            ############### 6. GENERATE REPORT ###############
            # TODO
            # from reporting import generate report

            ############### 7. SHOW REPORT ###############
            # TODO
            # ukazat v bashi
            # bash_cmd = echo "subor s reportom"
    except Exception as err:
        log("run testsuite | "+str(err)+" | "+str(traceback.format_exc()))
        env.set_exit_mode()

    return env


def prepare_data(env, solution_dir):
    if not env.cwd.proj or not solution_dir:
        return False

    # 1. check necessary dirs and files
    tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
    sum_file = os.path.join(tests_dir, SUM_FILE)
    scoring_file = os.path.join(tests_dir, SCORING_FILE)
    testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)
    if not os.path.exists(tests_dir) or not os.path.isdir(tests_dir):
        log(f"prepare data | tests_dir '{tests_dir}' doesnt exists or its not a directory")
        return False
    if not os.path.exists(scoring_file):
        log(f"prepare data | scoring file '{scoring_file}' doesnt exist")
        return False
    if not os.path.exists(sum_file):
        log(f"prepare data | sum file '{sum_file}' doesnt exist")
        return False
    if not os.path.exists(testsuite_file):
        log(f"prepare data | testsuite '{testsuite_file}' doesnt exist")
        return False
    if not os.access(testsuite_file, os.X_OK):
        log(f"prepare data | testsuite '{testsuite_file}' is not executable (try: chmod +x testsuite.sh)")
        return False

    # 2. check if tst fce file is in proj/tests/src/ dir
    bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)
    if not bash_tests_ok:
        log("prepare data | problem with bash functions for tests")
        return False

    # 3. copy data for testing to shared dir
    try:
        os.makedirs(SHARED_DIR, exist_ok=True)
        shutil.copytree(tests_dir, SHARED_TESTS_DIR) # proj/tests/ -> /docker_shared/tests/
        shutil.copytree(solution_dir, SHARED_SUT_DIR) # proj/xlogin/ -> /docker_shared/sut/
        shutil.copyfile(SRC_RUN_FILE, SHARED_RUN_FILE)
    except Exception as err:
        log("prepare data | copy data | "+str(err))
        return False

    return True



# return success
# ocakavam ze je vytvoreny image s menom `test`
def run_testsuite_in_docker(solution_dir, fut):
    succ = True
    try:
        # get user id
        # os.getuid() + os.getgid()
        USER = os.getenv('USER')
        is_root = False
        if USER =='root':
            is_root = True
        output = subprocess.run(f"id -u {USER}".split(' '), capture_output=True)
        user_id = output.stdout.decode('utf-8').strip()

        # create container from image `test` (IMAGE_NAME)

        # dat do jedneho commandu (run + bash)
        # funkcia: vytvor image s uzivatelom xy a uloz tento image pre dalsie pouzivanie (pre rozne alpine, fedora, centos,) 
        container_cid_file = '/tmp/docker.cid'
        out = subprocess.run(f"docker run --cidfile {container_cid_file} --rm -d --workdir {CONTAINER_DIR} -v {SHARED_DIR}:{CONTAINER_DIR}:z {IMAGE_NAME} bash -c".split(' ')+["while true; do sleep 1; done"],  capture_output=True)
        # log("docker run stdout | "+str(out.stdout.decode('utf-8')))
        # log("docker run stderr | "+str(out.stderr.decode('utf-8')))

        # add user in docker container (if user is not root)
        with open(container_cid_file, 'r') as f:
            cid = f.read()
        if not is_root:
            output = subprocess.run(f"docker exec {cid} useradd -u {user_id} test".split(' '), capture_output=True)

        # useradd alebo adduser

        # run test script (cd sut; /opt/tests/run.sh)
        # run_testsuite /opt/tests/src /opt/tests /opt/sut/tests_tags.yaml tests sut {fut}
        command = f"{CONTAINER_RUN_FILE} /opt/tests/src /opt/tests tests_tags.yaml {RESULTS_SUB_DIR} sut {fut}"
        output = subprocess.run(f"docker exec --user {user_id} --workdir {CONTAINER_SUT_DIR} {cid} bash {command}".split(' '), capture_output=True)
        result = output.stdout.decode('utf-8')
        err = output.stderr.decode('utf-8')

        # log("docker exec stdout | "+str(result))
        # log("docker exec stderr | "+str(err))

        # remove container
        out = subprocess.run(f"docker rm -f {cid}".split(' '), capture_output=True)

        # get results from test script
        docker_results = os.path.join(SHARED_SUT_DIR, RESULTS_SUB_DIR)
        student_results = os.path.join(solution_dir, RESULTS_SUB_DIR)
        shutil.copytree(docker_results, student_results, dirs_exist_ok=True)
    except Exception as err:
        log("run testsuite | "+str(err)+" | "+str(traceback.format_exc()))
        succ = False
    finally:
        try:
            # clear temporary files and dirs
            # rm -rf docker_shared
            # rm /tmp/docker.cid
            # docker rm -f {cid}
            os.remove(container_cid_file)
            shutil.rmtree(SHARED_DIR)
        except Exception as err:
            log("warning | remove shared dir & cid file | "+str(err)+" | "+str(traceback.format_exc()))

    return succ



def clean_test(solution_dir):
    try:
        student_results = os.path.join(solution_dir, RESULTS_SUB_DIR)
        if os.path.exists(student_results):
            shutil.rmtree(student_results)
        if os.path.exists(SHARED_DIR):
            shutil.rmtree(SHARED_DIR)
    except Exception as err:
        log("clean test | "+str(err))



def calculate_score(env, solution_dir):
    if not env.cwd.proj or not solution_dir:
        return None

    max_score = env.cwd.proj.max_score
    try:
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
            score = max_score if result > max_score else result
            bonus = result-max_score if result > max_score else 0
            return (score, bonus)
        else:
            log("calculate score sum | no tag from SUM equation was found")
            log("ignored tags: "+str(ignored_tags))
            return None
    except Exception as err:
        log("calculate score sum | "+str(err)+" | "+str(traceback.format_exc()))
        return None


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



def check_bash_functions_for_testing(proj_dir):
    bash_dir = os.path.join(proj_dir, TESTS_DIR, TST_FCE_DIR)
    bash_file = os.path.join(bash_dir, TST_FCE_FILE)
    bash_file_exists = False
    if os.path.exists(bash_file):
        bash_file_exists = True
    else:
        try:
            if not os.path.exists(bash_dir):
                os.mkdir(bash_dir)
            shutil.copyfile(SRC_BASH_FILE, bash_file)
            st = os.stat(bash_file)
            os.chmod(bash_file, st.st_mode | stat.S_IEXEC)
            bash_file_exists = True
        except Exception as err:
            log("copy bash functions | "+str(err))
    return bash_file_exists





# bin/t
""" /bin/t --> spusti /tests/testsuite.sh --- ten spusta /bin/tst run param """
# return success
def run_testsuite_in_local(tests_dir, solution_dir, fut):
    succ = True
    try:
        testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)
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
        command += f"export RESULTS_DIR={RESULTS_SUB_DIR}\n"
        command += f"export FUT={fut}\n"
        command += f"export login={login}\n"
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



# export FUT={fut}\n\



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

