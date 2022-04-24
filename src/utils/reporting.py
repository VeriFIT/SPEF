import re
import os
import glob
import traceback


from utils.logger import *
from utils.loading import *
from utils.match import *

from modules.project import Project



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
        dest_path = os.path.join(solution.path, "**", "*"+REPORT_SUFFIX)
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
                    code_review.append(str(note.text)+'\n')
    except Exception as err:
        log("gen code review | get report files | "+str(err)+" | "+str(traceback.format_exc()))
        return

    # save code review to file
    code_review_file = os.path.join(report_dir, CODE_REVIEW_FILE)
    with open(code_review_file, 'w+') as f:
        f.write('\n'.join(code_review))



def add_test_note_to_solutions(env, solutions, note_text):
    if env.cwd.proj is None:
        return

    # get current testsuite version
    tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
    testsuite_tags = load_testsuite_tags(tests_dir)
    if testsuite_tags is not None:
        args = testsuite_tags.get_args_for_tag("version")
        if args is not None and len(args)>0:
            version = int(args[0])
            for solution in solutions:
                # add test note
                solution.add_test_note(note_text, version)
                save_test_notes_for_solution(solution)