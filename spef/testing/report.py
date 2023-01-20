import glob
import os
import shutil
import traceback

from jinja2 import Environment, FileSystemLoader

from spef.testing.tst import calculate_score
from spef.utils.loading import *
from spef.utils.logger import *

REPORT_TEMPLATE_FILE = os.path.join(DATA_DIR, REPORT_TEMPLATE)


def copy_default_report_template(dst_file):
    try:
        shutil.copy(REPORT_TEMPLATE_FILE, dst_file)
    except Exception as err:
        log(f"copy default report template | {err} | {traceback.format_exc()}")


def get_supported_data_for_report():
    data = {
        "project_name": "name of this project (from project config)",
        "max_score": "maximum score for this project (from project config)",
        "total_score": "total solution score (calculated from sum file)",
        "bonus_score": "bonus solution score (calculated from sum file)",
        "test_results": "list of test results (each test has params: name, result, score, description and note)",
        "code_review": "list of notes from code review (each note has params: file, row, col and text)",
        "user_notes": "list of user specific notes to solution",
        "test_notes": "list of user notes related to automatic tests (for last testsuite version)",
        "solution_tags": "total copy of solution tags (from solution_tags file where tag = tag_name: [tag params])",
        "test_results_tags": """total copy of test results tags (from tests_tags file in solution directory)\
 - example of how to use tag from test results in report template: \
{% for param in test_results_tags.tag_name %}""",
    }
    return data


def get_data_for_report(env, solution):
    if not env.cwd.proj:
        return

    # get project data
    project_name = env.cwd.proj.name
    max_score = env.cwd.proj.max_score
    total_score = "-"
    bonus_score = "-"

    try:
        # get solution data
        s_tags = solution.tags
        if s_tags is not None and len(s_tags) > 0:
            score_args = s_tags.get_args_for_tag("score")
            bonus_args = s_tags.get_args_for_tag("score_bonus")
            if score_args is not None and len(score_args) > 0:
                total_score = score_args[0]
            else:
                scoring = calculate_score(env, solution)
                if scoring is not None:
                    total_score, bonus_score = scoring
            if bonus_args is not None and len(bonus_args) > 0:
                bonus_score = bonus_args[0]
            solution_tags = s_tags.data
        else:
            solution_tags = {}
    except Exception as err:
        log(
            f"get data for report | get solution data | {err} | {traceback.format_exc()}"
        )

    try:
        # get test results
        t_tags = solution.test_tags
        if t_tags is not None and len(t_tags) > 0:
            test_results_tags = t_tags.data

            test_names = get_tests_names(env)
            test_results = []
            for test_name in test_names:
                # for each test find tag with result
                #   #scoring_test1(body, popis testu, doplnujuce info)
                #   #test1_fail(pricina zlyhania)" "pricina zlyhania"
                #   #test1_ok()
                test_scoring_args = t_tags.get_args_for_tag(f"scoring_{test_name}")
                test_res_fail = t_tags.get_args_for_tag(f"{test_name}_fail")
                test_res_ok = t_tags.get_args_for_tag(f"{test_name}_ok")
                score, description, result, note = "-", "-", "-", "-"

                # add test to test results only if scoring exists
                if test_scoring_args is not None:
                    score = test_scoring_args[0] if len(test_scoring_args) > 0 else "-"
                    description = (
                        test_scoring_args[1] if len(test_scoring_args) > 1 else "-"
                    )
                    if test_res_fail is not None:
                        result = "fail"
                        note = test_res_fail[0] if len(test_res_fail) > 0 else "-"
                    elif test_res_ok is not None:
                        result = "ok"
                        note = test_res_ok[0] if len(test_res_ok) > 0 else "-"
                    else:
                        # if there is no tag with test result (fail/ok), continue to next test
                        continue
                    test_results.append(
                        {
                            "name": test_name,  # test_1
                            "result": result,  # ok
                            "score": score,  # 2
                            "description": description,  # this is first test
                            "note": note,  # this is note for test result (ex: failed bcs of timeout)
                        }
                    )
        else:
            test_results_tags = {}
            test_results = []
    except Exception as err:
        log(
            f"get data for report | get test results | {err} | {traceback.format_exc()}"
        )

    try:
        # get code review
        code_review = []
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

                    row = note.row if note.row is not None else "-"
                    col = note.col if note.col is not None else "-"
                    code_review.append(
                        {
                            "file": file_name,  # sut_file.c
                            "row": row,  # 14
                            "col": col,  # 5
                            "text": note.text,  # this is note to your code
                        }
                    )
    except Exception as err:
        log(f"get data for report | get code review | {err} | {traceback.format_exc()}")

    # get user notes
    user_notes = solution.user_notes

    # get current version of testsuite
    version = None
    tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
    testsuite_tags = load_testsuite_tags(tests_dir)
    if testsuite_tags is not None:
        # get testsuite version
        args = testsuite_tags.get_args_for_tag("version")
        if args is not None and len(args) > 0:
            version = int(args[0])

    # get test notes for current version of testsuite
    test_notes = []
    if version is not None:
        test_notes = solution.get_test_notes_for_version(version)

    # create dictionary with data for report template
    data = {
        # project
        "project_name": project_name,
        "max_score": max_score,
        # solution
        "total_score": total_score,
        "bonus_score": bonus_score,
        "test_results": test_results,
        "code_review": code_review,
        "user_notes": user_notes,
        "test_notes": test_notes,
        # total copy of tags
        "solution_tags": solution_tags,
        "test_results_tags": test_results_tags,
    }
    # log(data)
    return data


def generate_report_from_template(env, solution):
    if not env.cwd.proj:
        return

    # get data for report
    data = get_data_for_report(env, solution)
    if data:
        # get template
        report_dir = os.path.join(env.cwd.proj.path, REPORT_DIR)
        jinja_env = Environment(
            loader=FileSystemLoader(report_dir), trim_blocks=True, lstrip_blocks=True
        )
        template = jinja_env.get_template(REPORT_TEMPLATE)

        # generate report
        dest_report_dir = os.path.join(solution.path, REPORT_DIR)
        dest_report_file = os.path.join(dest_report_dir, TOTAL_REPORT_FILE)
        if not os.path.exists(dest_report_dir):
            os.makedirs(dest_report_dir)
        with open(dest_report_file, "w+") as f:
            result = template.render(data)
            f.write(result)
