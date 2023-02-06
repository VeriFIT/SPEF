# functions identification

CHANGE_SYSTEM_CONTROL = 1000
CHANGE_SYSTEM_CONFIG = 1001
BASH_SWITCH = 999

""" file (edit/manage) control """
EXIT_PROGRAM = 1
CHANGE_FOCUS = 2
RESIZE_WIN = 3
SHOW_HELP = 4
FILTER = 5

CURSOR_UP = 6
CURSOR_DOWN = 7
CURSOR_LEFT = 8
CURSOR_RIGHT = 9

SET_EDIT_FILE_MODE = 10
SET_MANAGE_FILE_MODE = 11
SHOW_OR_HIDE_TAGS = 12
SHOW_OR_HIDE_LINE_NUMBERS = 13
SHOW_OR_HIDE_NOTE_HIGHLIGHT = 14
SHOW_SUPPORTED_DATA = 15
SHOW_TYPICAL_NOTES = 16
OPEN_NOTE_MANAGEMENT = 17
ADD_CUSTOM_NOTE = 18
ADD_TYPICAL_NOTE = 19
GO_TO_PREV_NOTE = 20
GO_TO_NEXT_NOTE = 21
RELOAD_FILE_FROM_LAST_SAVE = 22
RELOAD_ORIGINAL_BUFF = 23

DELETE_CHAR = 30
BACKSPACE_CHAR = 31
PRINT_NEW_LINE = 32
PRINT_CHAR = 33
SAVE_FILE = 34


""" directory browsing control """
QUICK_VIEW_ON_OFF = 100
OPEN_FILE = 101
OPEN_MENU = 102
DELETE_FILE = 103
SHOW_OR_HIDE_CACHED_FILES = 104
SHOW_OR_HIDE_LOGS = 105
GO_TO_TAGS = 106
ENTER_DIRECTORY = 107
EXIT_DIRECTORY = 108

""" tag management control """
EDIT_TAG = 200
ADD_TAG = 201
DELETE_TAG = 202
OPEN_TAG_FILE = 203

""" note management control """
EXIT_NOTES = 300
EDIT_NOTE = 301
GO_TO_NOTE = 302
SAVE_AS_TYPICAL_NOTE = 303
DELETE_NOTE = 304

""" filter management control """
EXIT_FILTER = 400
SAVE_FILTER = 401
REMOVE_FILTER = 402
AGGREGATE_FILTER = 403

""" menu control """
EXIT_MENU = 500
SAVE_OPTION = 501
MOVE_LEFT = 502
MOVE_RIGHT = 503
SELECT_BY_IDX = 504
SELECT_OPTION = 505

""" user input control """
EXIT_USER_INPUT = 600
SAVE_INPUT = 601

CLEAR_LOG = 610


""" menu functions """
# anywhere
ADD_PROJECT = 700

EXPAND_HERE = 701
EXPAND_TO = 702
CREATE_DIR = 703
CREATE_FILE = 704
REMOVE_FILE = 705
RENAME_FILE = 706
COPY_FILE = 707
MOVE_FILE = 708

# in proj root dir
EDIT_PROJ_CONF = 710
SHOW_OR_HIDE_PROJ_INFO = 711
CREATE_DOCKERFILE = 712
CREATE_DOCKER_IMAGE = 713
EXPAND_AND_RENAME_SOLUTION = 714
EXPAND_ALL_SOLUTIONS = 715
RENAME_ALL_SOLUTIONS = 716
TEST_ALL_STUDENTS = 717
TEST_CLEAN_ALL = 718


# in solution dir
TEST_STUDENT = 720
TEST_CLEAN = 721
ALL_RUN_TESTS = 722
RUN_TESTS = 723
GEN_CODE_REVIEW = 724
GEN_TOTAL_REPORT = 725
ADD_TEST_NOTE = 726
ADD_USER_NOTE = 727
ADD_TEST_NOTE_TO_ALL = 728
ADD_USER_NOTE_TO_ALL = 729
ADD_TAG_TO_ALL = 730
CALCULATE_SUM_ALL = 731

SHOW_CODE_REVIEW = 740
SHOW_TEST_NOTES = 741
SHOW_USER_NOTES = 742
SHOW_TOTAL_REPORT = 743
SHOW_TEST_RESULTS = 744

SHOW_SCORING_STATS = 745
SHOW_TST_RES_STATS = 746

# in tests dir
ADD_TEST = 750
EDIT_TESTSUITE = 751
CHANGE_SCORING = 752
CHANGE_SUM = 753

# in tests/test dir
REMOVE_TEST = 760
EDIT_TEST = 761


#########################################################################
############## F U N C T I O N S    B Y    S H O R T C U T ##############
#########################################################################

""" mapping of functions from controls.yaml to intern representation of function id """


def map_file_function(str_fce):
    functions = {
        "show_help": SHOW_HELP,
        "exit_program": EXIT_PROGRAM,
        "bash_switch": BASH_SWITCH,
        "save_file": SAVE_FILE,
        "show_or_hide_tags": SHOW_OR_HIDE_TAGS,
        "show_or_hide_line_numbers": SHOW_OR_HIDE_LINE_NUMBERS,
        "show_or_hide_note_highlight": SHOW_OR_HIDE_NOTE_HIGHLIGHT,
        "open_note_management": OPEN_NOTE_MANAGEMENT,
        "reload_file_from_last_save": RELOAD_FILE_FROM_LAST_SAVE,
        "show_supported_data": SHOW_SUPPORTED_DATA,
        "show_typical_notes": SHOW_TYPICAL_NOTES,
        "set_edit_file_mode": SET_EDIT_FILE_MODE,
        "set_manage_file_mode": SET_MANAGE_FILE_MODE,
        "change_focus": CHANGE_FOCUS,
        "resize_win": RESIZE_WIN,
        "cursor_up": CURSOR_UP,
        "cursor_down": CURSOR_DOWN,
        "cursor_left": CURSOR_LEFT,
        "cursor_right": CURSOR_RIGHT,
        "delete": DELETE_CHAR,
        "backspace": BACKSPACE_CHAR,
        "print_new_line": PRINT_NEW_LINE,
        "print_char": PRINT_CHAR,
        "filter": FILTER,
        "add_custom_note": ADD_CUSTOM_NOTE,
        "add_typical_note": ADD_TYPICAL_NOTE,
        "go_to_prev_note": GO_TO_PREV_NOTE,
        "go_to_next_note": GO_TO_NEXT_NOTE,
        "reload_original_buff": RELOAD_ORIGINAL_BUFF,
    }
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_brows_function(str_fce):
    functions = {
        "show_help": SHOW_HELP,
        "exit_program": EXIT_PROGRAM,
        "bash_switch": BASH_SWITCH,
        "open_menu": OPEN_MENU,
        "quick_view_on_off": QUICK_VIEW_ON_OFF,
        "go_to_tags": GO_TO_TAGS,
        "show_or_hide_cached_files": SHOW_OR_HIDE_CACHED_FILES,
        "show_or_hide_logs": SHOW_OR_HIDE_LOGS,
        "open_file": OPEN_FILE,
        "delete_file": DELETE_FILE,
        "change_focus": CHANGE_FOCUS,
        "resize_win": RESIZE_WIN,
        "cursor_up": CURSOR_UP,
        "cursor_down": CURSOR_DOWN,
        "enter_directory": ENTER_DIRECTORY,
        "exit_directory": EXIT_DIRECTORY,
        "filter": FILTER,
    }
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_tags_function(str_fce):
    functions = {
        "show_help": SHOW_HELP,
        "exit_program": EXIT_PROGRAM,
        "bash_switch": BASH_SWITCH,
        "edit_tag": EDIT_TAG,
        "add_tag": ADD_TAG,
        "delete_tag": DELETE_TAG,
        "open_tag_file": OPEN_TAG_FILE,
        "change_focus": CHANGE_FOCUS,
        "resize_win": RESIZE_WIN,
        "cursor_up": CURSOR_UP,
        "cursor_down": CURSOR_DOWN,
        "filter": FILTER,
    }
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_notes_function(str_fce):
    functions = {
        "show_help": SHOW_HELP,
        "exit_program": EXIT_PROGRAM,
        "bash_switch": BASH_SWITCH,
        "edit_note": EDIT_NOTE,
        "add_custom_note": ADD_CUSTOM_NOTE,
        "add_typical_note": ADD_TYPICAL_NOTE,
        "show_typical_notes": SHOW_TYPICAL_NOTES,
        "go_to_note": GO_TO_NOTE,
        "save_as_typical_note": SAVE_AS_TYPICAL_NOTE,
        "delete_note": DELETE_NOTE,
        "exit_notes": EXIT_NOTES,
        "change_focus": CHANGE_FOCUS,
        "resize_win": RESIZE_WIN,
        "cursor_up": CURSOR_UP,
        "cursor_down": CURSOR_DOWN,
    }
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_filter_function(str_fce):
    functions = {
        "show_help": SHOW_HELP,
        "exit_program": EXIT_PROGRAM,
        "bash_switch": BASH_SWITCH,
        "aggregate": AGGREGATE_FILTER,
        "remove_filter": REMOVE_FILTER,
        "exit_filter": EXIT_FILTER,
        "cursor_up": CURSOR_UP,
        "cursor_down": CURSOR_DOWN,
        "cursor_left": CURSOR_LEFT,
        "cursor_right": CURSOR_RIGHT,
        "resize_win": RESIZE_WIN,
        "delete": DELETE_CHAR,
        "backspace": BACKSPACE_CHAR,
        "print_char": PRINT_CHAR,
        "save_filter": SAVE_FILTER,
    }
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_menu_function(str_fce):
    functions = {
        "show_help": SHOW_HELP,
        "exit_program": EXIT_PROGRAM,
        "bash_switch": BASH_SWITCH,
        "exit_menu": EXIT_MENU,
        "resize_win": RESIZE_WIN,
        "cursor_up": CURSOR_UP,
        "cursor_down": CURSOR_DOWN,
        "save_option": SAVE_OPTION,
        "select_by_idx": SELECT_BY_IDX,
        "select_option": SELECT_OPTION,
        "move_left": MOVE_LEFT,
        "move_right": MOVE_RIGHT,
    }
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_user_input_function(str_fce):
    functions = {
        "show_help": SHOW_HELP,
        "exit_program": EXIT_PROGRAM,
        "bash_switch": BASH_SWITCH,
        "exit_user_input": EXIT_USER_INPUT,
        "resize_win": RESIZE_WIN,
        "cursor_up": CURSOR_UP,
        "cursor_down": CURSOR_DOWN,
        "cursor_left": CURSOR_LEFT,
        "cursor_right": CURSOR_RIGHT,
        "delete": DELETE_CHAR,
        "backspace": BACKSPACE_CHAR,
        "save_input": SAVE_INPUT,
        "print_char": PRINT_CHAR,
        "move_left": MOVE_LEFT,
        "move_right": MOVE_RIGHT,
    }
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_user_logs_function(str_fce):
    functions = {
        "exit_program": EXIT_PROGRAM,
        "bash_switch": BASH_SWITCH,
        "open_file": OPEN_FILE,
        "clear_log": CLEAR_LOG,
        "change_focus": CHANGE_FOCUS,
        "resize_win": RESIZE_WIN,
        "cursor_up": CURSOR_UP,
        "cursor_down": CURSOR_DOWN,
    }
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


#########################################################################
################## F U N C T I O N S    I N    M E N U ##################
#########################################################################


# funkcie tykajuce sa nastavenia samotneho frameworku
def global_menu_functions():
    return {
        "open file with user control": CHANGE_SYSTEM_CONTROL,  # TODO otvori subor controls.yaml a znovu nacita controls
        "open file with framework configuration": CHANGE_SYSTEM_CONFIG,  # TODO otvori subor config.py a znovu nacita cely config
    }


# def get_menu_functions(dir_stack, in_proj_dir=False, in_solution_dir=False, is_test_dir=False):
def get_menu_functions(in_proj_dir=False, in_solution_dir=False, is_test_dir=False):
    basic = {
        "create new project here": ADD_PROJECT,
        "create new directory": CREATE_DIR,
        "create new file": CREATE_FILE
        # 'remove file': REMOVE_FILE,
        # 'rename file': RENAME_FILE,
        # 'copy file': COPY_FILE,
        # 'move file': MOVE_FILE
    }

    proj = {
        "project - edit configuration": EDIT_PROJ_CONF,
        "project - show/hide project info": SHOW_OR_HIDE_PROJ_INFO,
        "testing - create or edit Dockerfile": CREATE_DOCKERFILE,
        "testing - create Docker image for testing": CREATE_DOCKER_IMAGE,
        "all students - expand archives for all students": EXPAND_ALL_SOLUTIONS,
        "all students - name solution file correctly for all students": RENAME_ALL_SOLUTIONS,
        "all students - run tests (testsuite)": TEST_ALL_STUDENTS,
        "all students - clean from test results": TEST_CLEAN_ALL,
        "all students - select and run tests": ALL_RUN_TESTS,
        "all students - calculate score": CALCULATE_SUM_ALL,
        "all students - add test note related to automatic tests": ADD_TEST_NOTE_TO_ALL,
        "all students - add custom user note related to solution": ADD_USER_NOTE_TO_ALL,
        "all students - add tag to all solutions": ADD_TAG_TO_ALL,
    }

    tests = {
        "tests - create new test": ADD_TEST,
        "tests - create/edit testsuite": EDIT_TESTSUITE,
        "tests - change scoring": CHANGE_SCORING,
        "tests - change sum": CHANGE_SUM,
        "tests - edit test": EDIT_TEST,
    }

    test = {"test - remove test": REMOVE_TEST}

    student = {
        "student - expand archive and name solution file correctly": EXPAND_AND_RENAME_SOLUTION,
        "student - run tests (testsuite)": TEST_STUDENT,
        "student - clean from test results": TEST_CLEAN,
        "student - select and run tests": RUN_TESTS,
        "student - generate code review from notes": GEN_CODE_REVIEW,  # create /reports/code_review
        "student - generate total report": GEN_TOTAL_REPORT,  # create /reports/total_report
        "student - add test note related to automatic tests": ADD_TEST_NOTE,  # add to /reports/test_notes
        "student - add custom user note related to solution": ADD_USER_NOTE,  # add to /reports/user_notes
        "student - show code review": SHOW_CODE_REVIEW,
        "student - show test notes": SHOW_TEST_NOTES,
        "student - show user notes": SHOW_USER_NOTES,
        "student - show total report with score": SHOW_TOTAL_REPORT,
        "student - show test results": SHOW_TEST_RESULTS,
    }

    stats = {
        "show solution scoring stats": SHOW_SCORING_STATS,
        "show test results stats": SHOW_TST_RES_STATS,
    }

    result_dir = {}
    if in_solution_dir:  # in solution dir or in proj dir with selected solution
        result_dir.update(proj)
        result_dir.update(student)
        result_dir.update(stats)
        result_dir.update(tests)
        result_dir.update(basic)
    elif is_test_dir:  # in test dir or in tests dir with selected test
        result_dir.update(proj)
        result_dir.update(tests)
        result_dir.update(test)
        result_dir.update(stats)
        result_dir.update(basic)
    elif in_proj_dir:  # in proj dir
        result_dir.update(proj)
        result_dir.update(tests)
        result_dir.update(stats)
        result_dir.update(basic)
    else:
        result_dir.update(basic)

    return result_dir
