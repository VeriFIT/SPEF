
from utils.loading import *



def history_test_modified(proj_dir, test_name):

    history_dir = os.path.join(proj_dir, HISTORY_DIR)
    history_file = os.path.join(history_dir, HISTORY_FILE)

    tests_dir = os.path.join(proj_dir, TESTS_DIR)
    testcase_dir = os.path.join(tests_dir, test_name)

    # testcase_tags_file = ..
    # testcase_tags = ...

    # zisti test version z tagov testu
    # TODO

    # stary skopiruj do /history_dir/test_name/test_version//
    # TODO


    # inkrementuj verziu testu
    # TODO

    history_test_event(proj_dir, test_name, "modify test")




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
        if args is None or len(args) > 1:
            log("history new test | testsuite tags - cant find tag #version(int)")
        else:
            version = args[0]
            event = "create new test"
            add_event_to_tests_history(history_file, version+1, test_name, event)
            tags_file = os.path.join(tests_dir, TESTSUITE_TAGS)
            add_tag_to_file(tags_file, {"version": [version+1]})
    else:
        log("history new test | cant load testsuite tags ")


def add_event_to_tests_history(file_path, version, test, event):
    with open(file_path, 'a+', encoding='utf8') as f:
        f.write(f"{version}:{test}:{event}\n")
