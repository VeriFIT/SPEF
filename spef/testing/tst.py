import os
import shutil
import stat
import subprocess
import datetime
import traceback

import spef.utils.logger as logger
from spef.utils.loading import (
    load_testsuite_tags,
    save_tags_to_file,
    load_sum_equation_from_file,
)
from spef.utils.parsing import parse_sum_equation


CONTAINER_DIR = "/opt"
CONTAINER_TESTS_DIR = "/opt/tests"
CONTAINER_SUT_DIR = "/opt/sut/"
CONTAINER_RUN_FILE = "/opt/tests/run.sh"


SHARED_DIR = os.path.join(logger.TMP_DIR, "docker_shared")
SHARED_TESTS_DIR = os.path.join(logger.TMP_DIR, "docker_shared/tests")
SHARED_SUT_DIR = os.path.join(logger.TMP_DIR, "docker_shared/sut")
SHARED_RUN_FILE = os.path.join(logger.TMP_DIR, "docker_shared/tests/run.sh")

# shell functions
TST_FCE_DIR = "src"
TST_FCE_FILE = "tst"  # proj/tests/src/tst
SRC_BASH_FILE = os.path.join(logger.DATA_DIR, "tst.sh")
SRC_RUN_TESTSUITE_FILE = os.path.join(logger.DATA_DIR, "run_testsuite.sh")
SRC_RUN_TESTS_FILE = os.path.join(logger.DATA_DIR, "run_tests.sh")


def run_testsuite(
    env, solution, add_to_user_logs, with_logs=True, run_seq_tests=False, tests=None
):
    try:
        if not env.cwd.proj or not solution:
            logger.log("run testsuite | run from solution dir in some project dir")
            return env, False

        ############### 1. CHECK IF FUT EXISTS ###############
        fut_ready = False
        fut = env.cwd.proj.sut_required
        file_list = os.listdir(solution.path)
        if fut in file_list:
            # check if fut is executable
            fut_path = os.path.join(solution.path, fut)
            if not os.access(fut_path, os.X_OK):
                st = os.stat(fut_path)
                os.chmod(fut_path, st.st_mode | stat.S_IEXEC)
            fut_ready = True
        else:
            # add tag "missing sut file"
            logger.log(
                f"run testsuite | fut file '{fut}' doesnt exists in solution dir"
            )
            add_to_user_logs(
                env, "error", f"FUT '{fut}' doesnt exists in solution directory"
            )
            solution.tags.set_tag("scoring_missing_fut", [0])

        if fut_ready:
            ############### 2. CLEAN SOLUTION ###############
            if with_logs:
                add_to_user_logs(env, "info", f"cleaning tests results...")
            clean_test(solution)

            ############### 3. PREPARE DATA ###############
            if with_logs:
                add_to_user_logs(env, "info", f"preparing data for testing...")
            if run_seq_tests and tests:
                data_ok = prepare_data(env, solution.path, SRC_RUN_TESTS_FILE)
            else:
                data_ok = prepare_data(env, solution.path, SRC_RUN_TESTSUITE_FILE)
            if not data_ok:
                logger.log("run testsuite | problem with testing data")
                add_to_user_logs(env, "error", f"problem with testing data...")
                return env, False

            ############### 4. RUN TESTSUITE ###############
            f1, f2, f3 = with_logs, run_seq_tests, tests
            succ = run_testsuite_in_docker(
                env,
                solution.path,
                fut,
                add_to_user_logs,
                with_logs=f1,
                run_seq_tests=f2,
                tests=f3,
            )
            if not succ:
                logger.log("run testsuite | problem with testsuite run in docker")
                return env, False
            # reload tests tags for solution after testsuite is done
            solution.reload_test_tags()

            # get testsuite version and add tag "testsuite_version" to solution tags
            tests_dir = os.path.join(env.cwd.proj.path, logger.TESTS_DIR)
            tests_tags = load_testsuite_tags(tests_dir)
            if tests_tags is not None and len(tests_tags) > 0:
                version_args = tests_tags.get_args_for_tag("version")
                if version_args is not None:
                    tst_version = list(version_args)[0]
                    solution.tags.set_tag("testsuite_version", [tst_version])

        # get datetime and add tag "last_testing" to solution tags
        date_time = datetime.datetime.now().strftime("%d/%m/%y-%H:%M")
        solution.tags.set_tag("last_testing", [date_time])

        ############### 5. CALCULATE SCORE ###############
        total_score = calculate_score(env, solution)
        # if found some tags from sum equation
        if total_score is not None:
            score, bonus = total_score
            solution.tags.set_tag("score", [score])
            if bonus > 0:
                solution.tags.set_tag("score_bonus", [bonus])
        save_tags_to_file(solution.tags)

    except Exception as err:
        logger.log("run testsuite | " + str(err) + " | " + str(traceback.format_exc()))
        env.set_exit_mode()
        return env, False

    return env, True


def prepare_data(env, solution_dir, run_file):
    if not env.cwd.proj or not solution_dir:
        return False

    # 1. check necessary dirs and files
    tests_dir = os.path.join(env.cwd.proj.path, logger.TESTS_DIR)
    sum_file = os.path.join(tests_dir, logger.SUM_FILE)
    scoring_file = os.path.join(tests_dir, logger.SCORING_FILE)
    testsuite_file = os.path.join(tests_dir, logger.TESTSUITE_FILE)
    if not os.path.exists(tests_dir) or not os.path.isdir(tests_dir):
        logger.log(
            f"prepare data | tests_dir '{tests_dir}' doesnt exists or its not a directory"
        )
        return False
    if not os.path.exists(scoring_file):
        logger.log(f"prepare data | scoring file '{scoring_file}' doesnt exist")
        return False
    if not os.path.exists(sum_file):
        logger.log(f"prepare data | sum file '{sum_file}' doesnt exist")
        return False
    if not os.path.exists(testsuite_file):
        logger.log(f"prepare data | testsuite '{testsuite_file}' doesnt exist")
        return False
    if not os.access(testsuite_file, os.X_OK):
        st = os.stat(testsuite_file)
        os.chmod(testsuite_file, st.st_mode | stat.S_IEXEC)
        # log(f"prepare data | testsuite '{testsuite_file}' is not executable (try: chmod +x testsuite.sh)")
        # return False

    # 2. check if tst fce file is in proj/tests/src/ dir
    bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)
    if not bash_tests_ok:
        logger.log("prepare data | problem with bash functions for tests")
        return False

    # 3. copy data for testing to shared dir
    try:
        os.makedirs(SHARED_DIR, exist_ok=True)
        # proj/tests/ -> /docker_shared/tests/
        shutil.copytree(tests_dir, SHARED_TESTS_DIR)
        # proj/xlogin/ -> /docker_shared/sut/
        shutil.copytree(solution_dir, SHARED_SUT_DIR)
        shutil.copyfile(run_file, SHARED_RUN_FILE)
        os.mkdir(os.path.join(SHARED_SUT_DIR, logger.RESULTS_SUB_DIR))
    except Exception as err:
        logger.log("prepare data | copy data | " + str(err))
        return False

    return True


def prepare_data_for_static_testing(env, solution_dir):
    if not env.cwd.proj or not solution_dir:
        return False

    # 1. check necessary dirs and files
    tests_dir = os.path.join(env.cwd.proj.path, logger.TESTS_DIR)
    sum_file = os.path.join(tests_dir, logger.SUM_FILE)
    scoring_file = os.path.join(tests_dir, logger.SCORING_FILE)
    if not os.path.exists(tests_dir) or not os.path.isdir(tests_dir):
        logger.log(
            f"prepare data | tests_dir '{tests_dir}' doesnt exists or its not a directory"
        )
        return False
    if not os.path.exists(scoring_file):
        logger.log(f"prepare data | scoring file '{scoring_file}' doesnt exist")
        return False
    if not os.path.exists(sum_file):
        logger.log(f"prepare data | sum file '{sum_file}' doesnt exist")
        return False

    # 2. check if tst fce file is in proj/tests/src/ dir
    bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)
    if not bash_tests_ok:
        logger.log("prepare data | problem with bash functions for tests")
        return False
    return True


# return success
# ocakavam ze je vytvoreny image s menom `test`
def run_testsuite_in_docker(
    env,
    solution_dir,
    fut,
    add_to_user_logs,
    with_logs=True,
    run_seq_tests=False,
    tests=None,
):
    succ = True
    try:
        # create container from image `test` (IMAGE_NAME)
        if with_logs:
            add_to_user_logs(env, "info", f"creating docker container...")

        container_cid_file = "/tmp/docker.cid"
        if os.path.exists(container_cid_file):
            os.remove(container_cid_file)
        output = subprocess.run(
            f"docker run --cidfile {container_cid_file} --rm -d --workdir {CONTAINER_DIR} -v {SHARED_DIR}:{CONTAINER_DIR}:z {logger.IMAGE_NAME} bash -c".split(
                " "
            )
            + ["while true; do sleep 1; done"],
            capture_output=True,
        )
        output_out = str(output.stdout.decode("utf-8"))
        output_err = str(output.stderr.decode("utf-8"))
        logger.log(f"docker run stdout | {output_out}")
        logger.log(f"docker run stderr | {output_err}")
        if not output_err:
            with open(container_cid_file, "r") as f:
                cid = f.read()

            if with_logs:
                add_to_user_logs(env, "info", f"running testsuite...")

            if run_seq_tests and tests:
                # run_tests tst_file tests_dir TESTS_TAGS RESULTS_DIR login fut tests
                test_list = " ".join(tests)
                command = f"{CONTAINER_RUN_FILE} /opt/tests/src/tst /opt/tests tests_tags.yaml {logger.RESULTS_SUB_DIR} sut {fut} {test_list}"
            else:
                # run_testsuite /opt/tests/src /opt/tests /opt/sut/tests_tags.yaml tests sut {fut}
                command = f"{CONTAINER_RUN_FILE} /opt/tests/src /opt/tests tests_tags.yaml {logger.RESULTS_SUB_DIR} sut {fut}"

            output = subprocess.run(
                f"docker exec --workdir {CONTAINER_SUT_DIR} {cid} bash {command}".split(
                    " "
                ),
                capture_output=True,
            )
            result = output.stdout.decode("utf-8")
            err = output.stderr.decode("utf-8")
            logger.log("docker exec stdout | " + str(result))
            logger.log("docker exec stderr | " + str(err))

            # remove container
            out = subprocess.run(f"docker rm -f {cid}".split(" "), capture_output=True)

            if with_logs:
                add_to_user_logs(env, "info", f"getting results from tests...")

            # get results from test script
            docker_results = os.path.join(SHARED_SUT_DIR, logger.RESULTS_SUB_DIR)
            student_results = os.path.join(solution_dir, logger.RESULTS_SUB_DIR)
            shutil.copytree(docker_results, student_results, dirs_exist_ok=True)
        else:
            add_to_user_logs(env, "error", f"cannot create docker container...")
            succ = False
    except Exception as err:
        logger.log("run testsuite | " + str(err) + " | " + str(traceback.format_exc()))
        succ = False

    try:
        # clear temporary files and dirs
        # rm -rf docker_shared
        # rm /tmp/docker.cid
        # docker rm -f {cid}
        if os.path.exists(container_cid_file):
            os.remove(container_cid_file)
        if os.path.exists(SHARED_DIR):
            shutil.rmtree(SHARED_DIR)
    except Exception as err:
        logger.log(
            "warning | remove shared dir & cid file | "
            + str(err)
            + " | "
            + str(traceback.format_exc())
        )

    return succ


def clean_test(solution):
    try:
        student_results = os.path.join(solution.path, logger.RESULTS_SUB_DIR)
        if os.path.exists(student_results):
            shutil.rmtree(student_results)
        if os.path.exists(SHARED_DIR):
            shutil.rmtree(SHARED_DIR)
    except Exception as err:
        logger.log("clean test | " + str(err))


def calculate_score(env, solution):
    if not env.cwd.proj or not solution:
        return None

    max_score = env.cwd.proj.max_score
    try:
        # load sum file
        tests_dir = os.path.join(env.cwd.proj.path, logger.TESTS_DIR)
        sum_file = os.path.join(tests_dir, logger.SUM_FILE)
        sum_equation_str = load_sum_equation_from_file(env, sum_file)

        # parse sum equation
        equation, ignored_tags = parse_sum_equation(env, solution, sum_equation_str)
        equation = " ".join(str(x) for x in equation)

        # calculate sum
        if equation != "":
            result = eval(equation)
            score = max_score if result > max_score else result
            bonus = result - max_score if result > max_score else 0
            return (score, bonus)
        else:
            logger.log("calculate score sum | no tag from SUM equation was found")
            logger.log("ignored tags: " + str(ignored_tags))
            return None
    except Exception as err:
        logger.log(
            "calculate score sum | " + str(err) + " | " + str(traceback.format_exc())
        )
        return None


def check_bash_functions_for_testing(proj_dir):
    bash_dir = os.path.join(proj_dir, logger.TESTS_DIR, TST_FCE_DIR)
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
            logger.log("copy bash functions | " + str(err))
    return bash_file_exists
