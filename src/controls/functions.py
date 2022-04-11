# functions identification

BASH_SWITCH = 1000


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
SHOW_TYPICAL_NOTES = 15
OPEN_NOTE_MANAGEMENT = 16
ADD_CUSTOM_NOTE = 17
ADD_TYPICAL_NOTE = 18
GO_TO_PREV_NOTE = 19
GO_TO_NEXT_NOTE = 20
RELOAD_FILE_FROM_LAST_SAVE = 21
RELOAD_ORIGINAL_BUFF = 22

DELETE = 23
BACKSPACE = 24
PRINT_NEW_LINE = 25
PRINT_CHAR = 26
SAVE_FILE = 27


""" directory browsing control """
QUICK_VIEW_ON_OFF = 100
OPEN_FILE = 101
OPEN_MENU = 102
DELETE_FILE = 103
SHOW_OR_HIDE_CACHED_FILES = 104
GO_TO_TAGS = 105

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

""" menu control """
EXIT_MENU = 500
SAVE_OPTION = 501
MOVE_LEFT = 502
MOVE_RIGHT = 503

""" user input control """
EXIT_USER_INPUT = 600
SAVE_INPUT = 601


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
EXPAND_AND_RENAME_SOLUTION = 712
EXPAND_ALL_SOLUTIONS = 713
RENAME_ALL_SOLUTIONS = 714
TEST_ALL_STUDENTS = 715

SHOW_STATS = 716
SHOW_HISTOGRAM = 717

# in solution dir
TEST_STUDENT = 720
TEST_CLEAN = 721
GEN_CODE_REVIEW = 722
GEN_AUTO_REPORT = 723
ADD_AUTO_NOTE = 724
ADD_USER_NOTE = 725
SHOW_CODE_REVIEW = 726
SHOW_AUTO_REPORT = 727
SHOW_TOTAL_REPORT = 728
SHOW_TEST_RESULTS = 729

# in tests dir
ADD_TEST = 730
EDIT_TESTSUITE = 731
CHANGE_SCORING = 732
DEFINE_TEST_FAILURE = 733

# in tests/test dir
REMOVE_TEST = 734
EDIT_TEST = 735



#########################################################################
############## F U N C T I O N S    B Y    S H O R T C U T ##############
#########################################################################

""" mapping of functions from controls.yaml to intern representation of function id """
def map_file_function(str_fce):
    functions = {
        'exit_program': EXIT_PROGRAM,
        'bash_switch': BASH_SWITCH,
        'show_help': SHOW_HELP,
        'save_file': SAVE_FILE,
        'show_or_hide_tags': SHOW_OR_HIDE_TAGS,
        'set_edit_file_mode': SET_EDIT_FILE_MODE,
        'show_or_hide_line_numbers': SHOW_OR_HIDE_LINE_NUMBERS,
        'show_or_hide_note_highlight': SHOW_OR_HIDE_NOTE_HIGHLIGHT,
        'open_note_management': OPEN_NOTE_MANAGEMENT,
        'reload_file_from_last_save': RELOAD_FILE_FROM_LAST_SAVE,
        'show_typical_notes': SHOW_TYPICAL_NOTES,
        'set_manage_file_mode': SET_MANAGE_FILE_MODE,
        'change_focus': CHANGE_FOCUS,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'cursor_left': CURSOR_LEFT,
        'cursor_right': CURSOR_RIGHT,
        'delete': DELETE,
        'backspace': BACKSPACE,
        'print_new_line': PRINT_NEW_LINE,
        'print_char': PRINT_CHAR,
        'filter': FILTER,
        'add_custom_note': ADD_CUSTOM_NOTE,
        'add_typical_note': ADD_TYPICAL_NOTE,
        'go_to_prev_note': GO_TO_PREV_NOTE,
        'go_to_next_note': GO_TO_NEXT_NOTE,
        'reload_original_buff': RELOAD_ORIGINAL_BUFF}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_brows_function(str_fce):
    functions = {
        'exit_program': EXIT_PROGRAM,
        'bash_switch': BASH_SWITCH,
        'show_help': SHOW_HELP,
        'open_menu': OPEN_MENU,
        'quick_view_on_off': QUICK_VIEW_ON_OFF,
        'go_to_tags': GO_TO_TAGS,
        'show_or_hide_cached_files': SHOW_OR_HIDE_CACHED_FILES,
        'open_file': OPEN_FILE,
        'delete_file': DELETE_FILE,
        'change_focus': CHANGE_FOCUS,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'cursor_left': CURSOR_LEFT,
        'cursor_right': CURSOR_RIGHT,
        'filter': FILTER}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_tags_function(str_fce):
    functions = {
        'exit_program': EXIT_PROGRAM,
        'bash_switch': BASH_SWITCH,
        'show_help': SHOW_HELP,
        'edit_tag': EDIT_TAG,
        'add_tag': ADD_TAG,
        'delete_tag': DELETE_TAG,
        'open_tag_file': OPEN_TAG_FILE,
        'change_focus': CHANGE_FOCUS,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'filter': FILTER}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_notes_function(str_fce):
    functions = {
        'exit_program': EXIT_PROGRAM,
        'bash_switch': BASH_SWITCH,
        'show_help': SHOW_HELP,
        'edit_note': EDIT_NOTE,
        'add_custom_note': ADD_CUSTOM_NOTE,
        'add_typical_note': ADD_TYPICAL_NOTE,
        'go_to_note': GO_TO_NOTE,
        'save_as_typical_note': SAVE_AS_TYPICAL_NOTE,
        'delete_note': DELETE_NOTE,
        'exit_notes': EXIT_NOTES,
        'change_focus': CHANGE_FOCUS,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_filter_function(str_fce):
    functions = {
        'exit_program': EXIT_PROGRAM,
        'bash_switch': BASH_SWITCH,
        'show_help': SHOW_HELP,
        'remove_filter': REMOVE_FILTER,
        'exit_filter': EXIT_FILTER,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'cursor_left': CURSOR_LEFT,
        'cursor_right': CURSOR_RIGHT,
        'resize_win': RESIZE_WIN,
        'delete': DELETE,
        'backspace': BACKSPACE,
        'print_char': PRINT_CHAR,
        'save_filter': SAVE_FILTER}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_menu_function(str_fce):
    functions = {
        'exit_program': EXIT_PROGRAM,
        'bash_switch': BASH_SWITCH,
        'exit_menu': EXIT_MENU,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'save_option': SAVE_OPTION,
        'move_left': MOVE_LEFT,
        'move_right': MOVE_RIGHT}
    if str_fce in functions:
        return functions[str_fce]
    else:
        return None


def map_user_input_function(str_fce):
    functions = {
        'exit_program': EXIT_PROGRAM,
        'bash_switch': BASH_SWITCH,
        'exit_user_input': EXIT_USER_INPUT,
        'resize_win': RESIZE_WIN,
        'cursor_up': CURSOR_UP,
        'cursor_down': CURSOR_DOWN,
        'cursor_left': CURSOR_LEFT,
        'cursor_right': CURSOR_RIGHT,
        'delete': DELETE,
        'backspace': BACKSPACE,
        'save_input': SAVE_INPUT,
        'print_char': PRINT_CHAR,
        'move_left': MOVE_LEFT,
        'move_right': MOVE_RIGHT}
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
        'open file with user control': ADD_PROJECT, # TODO otvori subor controls.yaml a znovu nacita controls
        'open file with framework configuration': ADD_PROJECT # TODO otvori subor config.py a znovu nacita cely config
    }


def brows_menu_functions():
    return {
        'project - create new': ADD_PROJECT,
        'project - edit configuration': EDIT_PROJ_CONF,
        'project - show/hide project info': SHOW_OR_HIDE_PROJ_INFO, #       TODO zobrazit info o projekte
        'archive - expand all student solutions': EXPAND_ALL_SOLUTIONS, #   TODO rozbali vsetkych studentov
        'solution - name solution files correctly': RENAME_ALL_SOLUTIONS, # TODO premenuje vsetkych studentov
        'test - test all students': TEST_ALL_STUDENTS, #                    TODO testovat vsetkych studentov v proj root dir (alebo len filtrovanych studentov)
        'show statistics': SHOW_STATS, #                                    TODO zobrazit statistiky z testov
        'show histogram': SHOW_HISTOGRAM, #                                 TODO zobrazit histogram z testov
        'archive - expand solution and name it correctly': EXPAND_AND_RENAME_SOLUTION, #    TODO rozbali archiv a pomenuje ho spravne
        'test - test the student': TEST_STUDENT, #                                          TODO spusti testsuite
        'test - clean from test results': TEST_CLEAN, #                                     TODO vycisti archiv od bordelu z testov
        'show test results': SHOW_TEST_RESULTS, #                               TODO ukaze vysledky testov (zoznam testov medzi ktorymi sa da prechadzat) 
        'show auto report': SHOW_AUTO_REPORT, #                                 TODO ukaze subor s hodnotenim z auto testov
        'show code review notes': SHOW_CODE_REVIEW, #                           TODO ukaze subor s poznamkami z code review
        'show total report with score': SHOW_TOTAL_REPORT, #                    TODO ukaze celkove hodnotenie
        'report - generate code review from notes': GEN_CODE_REVIEW,
        'create new test': ADD_TEST, #                  TODO vytvori novy adresar testxx (adresar ktory este neexistuje) v nom bude subor runtest.sh
        'create or edit testsuite': EDIT_TESTSUITE, #   TODO otvori tests/testsuite.sh
        'define test failure': DEFINE_TEST_FAILURE, #   TODO definicia sposobu zlyhania testu
        'remove test': REMOVE_TEST, #   TODO odstrani cely adresar s testom a skontroluje testsuite ci tam nie je pouzity
        'edit test': EDIT_TEST, #       TODO otvori subor runtest.sh
        'expand archive here': EXPAND_HERE,
        'expand archive to ...': EXPAND_TO,
        'create directory': CREATE_DIR,
        'create file': CREATE_FILE,
        'remove file': REMOVE_FILE,
        'rename file': RENAME_FILE,
        'copy file': COPY_FILE,
        'move file': MOVE_FILE
    }


# def get_menu_functions(dir_stack, in_proj_dir=False, in_solution_dir=False, is_test_dir=False):
def get_menu_functions(in_proj_dir=False, in_solution_dir=False, is_test_dir=False):

    basic = {
        'create new project here': ADD_PROJECT,
        'expand archive here': EXPAND_HERE,
        'expand archive to ...': EXPAND_TO,
        'create new directory': CREATE_DIR,
        'create new file': CREATE_FILE,
        'remove file': REMOVE_FILE,
        'rename file': RENAME_FILE,
        'copy file': COPY_FILE,
        'move file': MOVE_FILE
    }

    proj = {
        'project - edit configuration': EDIT_PROJ_CONF,
        'project - show/hide project info': SHOW_OR_HIDE_PROJ_INFO,
        'student - expand archive and name solution file correctly': EXPAND_AND_RENAME_SOLUTION,
        'all students - expand archives for all students': EXPAND_ALL_SOLUTIONS,
        'all students - name solution file correctly for all students': RENAME_ALL_SOLUTIONS,
        'all students - run tests (testsuite)': TEST_ALL_STUDENTS
    }

    tests = {
        'tests - create new test': ADD_TEST,
        'tests - create/edit testsuite': EDIT_TESTSUITE,
        'tests - change scoring': CHANGE_SCORING,
        'tests - define test failure': DEFINE_TEST_FAILURE
    }

    test = {
        'test - remove test': REMOVE_TEST,
        'test - edit test': EDIT_TEST
    }

    stats = {
        'show statistics': SHOW_STATS,
        'show histogram': SHOW_HISTOGRAM
    }

    student = {
        'student - run tests (testsuite)': TEST_STUDENT,
        'student - clean from test results': TEST_CLEAN,
        'student - generate code review from notes': GEN_CODE_REVIEW,
        'student - generate auto report from tests': GEN_AUTO_REPORT, # TODO
        'student - add note to auto report': ADD_AUTO_NOTE, # TODO
        'student - add custom user note': ADD_USER_NOTE, # TODO
        'student - show code review notes': SHOW_CODE_REVIEW,
        'student - show auto report': SHOW_AUTO_REPORT,
        'student - show total report with score': SHOW_TOTAL_REPORT,
        'student - show test results': SHOW_TEST_RESULTS
    }


    result_dir = {}
    if in_solution_dir: # in solution dir or in proj dir with selected solution
        result_dir.update(proj)
        result_dir.update(student)
        result_dir.update(stats)
        result_dir.update(basic)
    elif is_test_dir: # in test dir or in tests dir with selected test
        result_dir.update(proj)
        result_dir.update(tests)
        result_dir.update(test)
        result_dir.update(stats)
        result_dir.update(basic)
    elif in_proj_dir: # in proj dir
        result_dir.update(proj)
        result_dir.update(tests)
        result_dir.update(stats)
        result_dir.update(basic)
    else:
        result_dir.update(basic)

    return result_dir


