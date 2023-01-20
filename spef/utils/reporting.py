import glob
import os
import traceback

from spef.modules.project import Project
from spef.testing.tst import calculate_score
from spef.utils.logger import *
from spef.utils.loading import *
from spef.utils.match import *


""" from subjA/proj1/xlogin00/dir/file_name to proj1/xlogin00/dir/file_name """


def get_path_relative_to_project_dir(dest_path, proj_path=None):
    # check if its project subdir
    cur_dir = dest_path if os.path.isdir(dest_path) else os.path.dirname(dest_path)
    if not proj_path:
        proj = None
        while True:
            file_list = os.listdir(cur_dir)
            parent_dir = os.path.dirname(cur_dir)
            if PROJ_CONF_FILE in file_list:
                proj_data = load_proj_from_conf_file(cur_dir)
                proj = Project(cur_dir)
                succ = proj.set_values_from_conf(proj_data)
                if not succ:
                    proj = None
                break
            else:
                if cur_dir == parent_dir:
                    break
                else:
                    cur_dir = parent_dir
        if proj is None:
            return None
        proj_path = proj.path

    # return relative path
    return os.path.relpath(dest_path, os.path.dirname(proj_path))


""" from subjA/proj1/xlogin00/dir/file_name to xlogin00/dir/file_name """


def get_path_relative_to_solution_dir(dest_path):
    # check if its project subdir
    proj = None
    cur_dir = dest_path if os.path.isdir(dest_path) else os.path.dirname(dest_path)
    while True:
        file_list = os.listdir(cur_dir)
        parent_dir = os.path.dirname(cur_dir)
        if PROJ_CONF_FILE in file_list:
            proj_data = load_proj_from_conf_file(cur_dir)
            proj = Project(cur_dir)
            succ = proj.set_values_from_conf(proj_data)
            if not succ:
                proj = None
            break
        else:
            if cur_dir == parent_dir:
                break
            else:
                cur_dir = parent_dir
    if proj is None:
        return None

    # find solution dir
    solution_dir = None
    if match_regex(proj.solution_id, os.path.basename(dest_path)):
        solution_dir = dest_path
    else:
        solution_dir = get_parent_regex_match(proj.solution_id, dest_path)
    if solution_dir is None:
        return None

    # return relative path
    return os.path.relpath(dest_path, os.path.dirname(solution_dir))


def generate_code_review(env, solution):
    if not env.cwd.proj or not solution:
        log("generate code review | current directory is not project (sub)directory")
        return

    # create dir for reports if not exists
    report_dir = os.path.join(solution.path, REPORT_DIR)
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    # process all notes from code review
    code_review = []
    try:
        dest_path = os.path.join(solution.path, "**", "*" + REPORT_SUFFIX)
        for report_file in glob.glob(dest_path, recursive=True):
            if os.path.isfile(report_file):
                report = load_report_from_file(report_file, add_suffix=False)
                for note in report.data:
                    if report.orig_file_name is not None:
                        file_name = report.orig_file_name[:-1]
                    else:
                        file_name = os.path.relpath(report.path, solution.name)
                        file_name = str(file_name).removesuffix(REPORT_SUFFIX)
                    if note.row is not None and note.col is not None:
                        code_review.append(f"{file_name}:{note.row}:{note.col}")
                    else:
                        code_review.append(f"{file_name}")
                    code_review.append(str(note.text) + "\n")
    except Exception as err:
        log(
            "gen code review | get report files | "
            + str(err)
            + " | "
            + str(traceback.format_exc())
        )
        return

    # save code review to file
    code_review_file = os.path.join(report_dir, CODE_REVIEW_FILE)
    with open(code_review_file, "w+") as f:
        f.write("\n".join(code_review))


def add_test_note_to_solutions(env, solutions, note_text):
    if env.cwd.proj is None:
        return

    # get current testsuite version
    tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
    testsuite_tags = load_testsuite_tags(tests_dir)
    if testsuite_tags is not None:
        args = testsuite_tags.get_args_for_tag("version")
        if args is not None and len(args) > 0:
            version = int(args[0])
            for solution in solutions:
                # add test note
                solution.add_test_note(note_text, version)
                save_test_notes_for_solution(solution)


"""
graf bodoveho hodnotenia (rozlozenie - kolko studentov spada do danej bodovej kategorie)
"""


def generate_scoring_stats(env):
    if env.cwd.proj is None:
        return

    sum_score = 0
    scored_solutions = 0
    nonzero_scored_solutions = 0

    try:
        scoring_severity = {}
        for key, solution in env.cwd.proj.solutions.items():
            # get score for solution
            total_score = None
            if solution.tags is not None and len(solution.tags) > 0:
                score_args = solution.tags.get_args_for_tag("score")
                if score_args is not None and len(score_args) > 0:
                    total_score = int(score_args[0])
                else:
                    scoring = calculate_score(env, solution)
                    if scoring is not None:
                        total_score, bonus_score = scoring

            # for each score, calculate its severity
            if total_score is not None:
                score = int(total_score)
                sum_score += score
                scored_solutions += 1
                if score > 0:
                    nonzero_scored_solutions += 1
                if score in scoring_severity:
                    scoring_severity[score] += 1
                else:
                    scoring_severity[score] = 1

        for i in range(0, env.cwd.proj.max_score + 1):
            if not i in scoring_severity:
                scoring_severity[i] = 0

        scoring_severity = dict(sorted(scoring_severity.items()))
        average = round(sum_score / scored_solutions, 2) if scored_solutions > 0 else 0
        nonzero_average = (
            round(sum_score / nonzero_scored_solutions, 2)
            if nonzero_scored_solutions > 0
            else 0
        )
        modus = max(scoring_severity, key=scoring_severity.get)
        shift = len(str(env.cwd.proj.max_score)) + 1
        highest_score = max(list(scoring_severity.values()))

        severity = ""
        for key, value in scoring_severity.items():
            # norm_val = int((value/highest_score)*10) if highest_score>0 else 0
            norm_val = int(value)
            space = " " * (shift - len(str(key)))
            stars = "*" * norm_val
            severity += f"{key}:{space}{stars} {value}\n"

        statistics = f"""\
Maximum score: {env.cwd.proj.max_score}
------------------------------------
Average: {average}
Average (without zero): {nonzero_average}
Modus: {modus}
------------------------------------
Scoring severity:
{severity}
"""
        # save stats to file
        report_dir = os.path.join(env.cwd.proj.path, REPORT_DIR)
        if not os.path.exists(report_dir) or not os.path.isdir(report_dir):
            os.makedirs(report_dir)

        stats_file = os.path.join(report_dir, SCORING_STATS_FILE)
        with open(stats_file, "w+") as f:
            f.write(statistics)
    except Exception as err:
        log(f"generate stats | {err} | {traceback.format_exc()}")


"""
histogram vysledkov testov (ktore testy boli ako hodnotene)
"""


def generate_test_results_hist(env):
    if env.cwd.proj is None:
        return

    max_score = env.cwd.proj.max_score
    score_nums = set()
    tests_stats = {}  # {'test_name': {'0': x%, '1': x,...}, 'test_name': {...},...}
    total_score_stats = {}  # {'score'}
    try:
        ################### TESTS STATS ###################
        tests = get_tests_names(env)
        for test_name in tests:
            test_scoring_severity = {}
            tested_solutions = 0
            # find scoring of this test for each solution
            for key, solution in env.cwd.proj.solutions.items():
                # get test result scoring for solution
                test_score = None
                if solution.test_tags is not None and len(solution.test_tags) > 0:
                    score_args = solution.test_tags.get_args_for_tag(
                        f"scoring_{test_name}"
                    )
                    if score_args is not None and len(score_args) > 0:
                        test_score = int(score_args[0])
                        tested_solutions += 1
                        score_nums.add(test_score)
                        if test_score in test_scoring_severity:
                            test_scoring_severity[test_score] += 1
                        else:
                            test_scoring_severity[test_score] = 1

            # parse scoring severity to percentage
            test_scoring_percentage = {}
            for score, severity in test_scoring_severity.items():
                test_scoring_percentage[score] = int(
                    (severity / tested_solutions) * 100
                )

            tests_stats[test_name] = test_scoring_percentage

        ################### TOTAL SCORE STATS ###################
        # get total score for solution
        scored_solutions = 0
        total_score_severity = {}
        for key, solution in env.cwd.proj.solutions.items():
            score_sum = None
            if solution.tags is not None and len(solution.tags) > 0:
                score_args = solution.tags.get_args_for_tag("score")
                if score_args is not None and len(score_args) > 0:
                    score_sum = int(score_args[0])
                else:
                    scoring = calculate_score(env, solution)
                    if scoring is not None:
                        score_sum, bonus_score = scoring
            if score_sum is not None:
                scored_solutions += 1
                if score_sum in total_score_severity:
                    total_score_severity[score_sum] += 1
                else:
                    total_score_severity[score_sum] = 1

        # parse total score to percentage
        for score, severity in total_score_severity.items():
            total_score_stats[score] = int((severity / scored_solutions) * 100)

        ################### PRINT STATISTICS ###################
        max_len_tst_name = int(max([len(str(tst_name)) for tst_name in tests_stats]))

        # all scoring numbers
        score_nums = sorted(score_nums)
        score_n = ""
        for num in score_nums:
            max_len = int(max(len(str(num) + "b"), len("100%")))
            space = " " * (max_len - (len(str(num) + "b")))
            score_n += f" {num}b{space} |"

        # scoring percentage for each test
        tests_res = ""
        tests_stats = dict(sorted(tests_stats.items()))
        for test_name, scoring in tests_stats.items():
            percentage = ""
            for num in score_nums:
                score = scoring[num] if num in scoring else 0
                max_len = int(max(len(str(num) + "b"), len("100%")))
                space = " " * (max_len - (len(str(score) + "%")))
                percentage += f" {score}%{space} |"
            space = " " * (max_len_tst_name - len(test_name))
            tests_res += f"{test_name}{space} |{percentage}\n"

        # total scoring percentage
        sum_n = ""
        sum_res = ""
        total_score_stats = dict(sorted(total_score_stats.items()))
        for number, percentage in total_score_stats.items():
            max_len = int(max(len(str(number) + "b"), len("100%")))
            space_n = " " * (max_len - (len(str(number) + "b")))
            space_res = " " * (max_len - (len(str(percentage) + "%")))
            sum_n += f"{number}b{space_n} |"
            sum_res += f"{percentage}%{space_res} |"

        space = " " * (max_len_tst_name - len("Test name"))
        line = "-" * (
            max(len(f"Test name{space} |{score_n}"), len(f"Total score |{score_n}"))
        )
        statistics = f"""\
Test name{space} |{score_n}
{line}
{tests_res}{line}
            |{sum_n}
Total score |{sum_res}
"""
        # save stats to file
        report_dir = os.path.join(env.cwd.proj.path, REPORT_DIR)
        if not os.path.exists(report_dir) or not os.path.isdir(report_dir):
            os.makedirs(report_dir)

        stats_file = os.path.join(report_dir, TESTS_STATS_FILE)
        with open(stats_file, "w+") as f:
            f.write(statistics)
    except Exception as err:
        log(f"generate stats | {err} | {traceback.format_exc()}")
