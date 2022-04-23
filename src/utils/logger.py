import datetime
import os

from pathlib import Path


ESC = 27


HOME = str(Path(__file__).parents[1])
LOG_FILE = os.path.join(HOME,"debug.log")
TMP_DIR = os.path.join(HOME,'tmp')


REPORT_SUFFIX = "_report.yaml"
TAGS_SUFFIX = "_tags.yaml"

# system files
CONFIG_FILE = "config.yaml"
CONTROL_FILE = "control.yaml"
TYPICAL_NOTES_FILE = "typical_notes.txt"

# proj/
PROJ_CONF_FILE = "proj_conf.yaml"
REPORT_DIR = "reports"
TESTS_DIR = "tests"
HISTORY_DIR = "history"

# proj/REPORT_DIR/
MAIL_TEXT = "mail.txt"
REPROT_TEMPLATE = "report_template.jinja"

# proj/HISTORY_DIR/
HISTORY_FILE = "testsuite_history.txt"

# proj/TESTS_DIR/
SUM_FILE = "sum"
SCORING_FILE = "scoring"
TESTSUITE_FILE = "testsuite.sh"
TEST_FILE = "dotest.sh"
TESTSUITE_TAGS = "testsuite"+TAGS_SUFFIX
TESTCASE_TAGS = "test"+TAGS_SUFFIX

# proj/solution/
SOLUTION_TAGS = "solution"+TAGS_SUFFIX

# proj/solution/TESTS_DIR/
TESTS_TAGS = "tests"+TAGS_SUFFIX

# proj/solution/REPORT_DIR/
CODE_REVIEW_FILE = "code_review"
USER_NOTES_FILE = "user_notes"
TOTAL_REPORT_FILE = "total_report"

# docker mapping
IMAGE_NAME = 'test'
RUN_FILE = 'run.sh'
DOCKER_SUT_DIR = 'sut'
RESULTS_SUB_DIR = 'tests'


# printing messages
EXIT_WITHOUT_SAVING = """WARNING: Exit without saving.\n\
    Press F2 to save and exit.\n\
    Press {} to force exiting without saving.\n\
    Press any other key to continue editing your file."""

TEST_MODIFICATION = """Modified test file - do you want to save test history?\n\
    Press F2 to save the old test version to history.\n\
    Press any other key to continue without saving...(old test version will be discard on system exit)"""

RELOAD_FILE_WITHOUT_SAVING = """WARNING: Reload file will discard changes.\n\
    Press F2 to save changes.\n\
    Press {} to reload file and discard all changes.\n\
    Press any other key to continue editing your file."""

EMPTY_PATH_FILTER_MESSAGE = "add path filter... ex: test1/unit "
EMPTY_CONTENT_FILTER_MESSAGE = "add content filter... ex: def test1 "
EMPTY_TAG_FILTER_MESSAGE = "add tag filter... ex: plagiat(^[0-5]$) "


def log(message):
    day = datetime.date.today()
    time = datetime.datetime.now().strftime("%X")
    with open(LOG_FILE, 'a') as f:
        f.write("{} {} | {}\n".format(day,time,message))

