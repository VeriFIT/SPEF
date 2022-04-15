import datetime
import os

from pathlib import Path


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


CONTAINER_DIR = '/opt'
CONTAINER_TESTS_DIR = os.path.join(CONTAINER_DIR, TESTS_DIR) # /opt/tests/
CONTAINER_SUT_DIR = os.path.join(CONTAINER_DIR, DOCKER_SUT_DIR) # /opt/sut/
CONTAINER_RUN_FILE = os.path.join(CONTAINER_TESTS_DIR, RUN_FILE) # /opt/tests/run.sh

SHARED_DIR = os.path.join(TMP_DIR, 'docker_shared')
SHARED_TESTS_DIR = os.path.join(SHARED_DIR, TESTS_DIR) # .../docker_shared/tests/
SHARED_SUT_DIR = os.path.join(SHARED_DIR, DOCKER_SUT_DIR) # .../docker_shared/sut/
SHARED_RUN_FILE = os.path.join(SHARED_TESTS_DIR, RUN_FILE) # .../docker_shared/tests/run.sh

# shell functions
TST_FCE_DIR = 'src' # .../src/
TST_FCE_FILE = os.path.join(TESTS_DIR, TST_FCE_DIR, 'tst') # .../tests/src/tst
SRC_BASH_FILE = os.path.join(HOME, 'testing', 'tst_orig.sh') # .../testing/tst_orig.sh


# TODO: SRC_BASH_FILE rozdelit na dva subory: podpora pre "dotest.sh" a funkcie pre "testsuite.sh"

# funkcie pre "testsuite.sh" a "dotest.sh" su v "tests/src/tst" (tst run, tst sum, tst clean,...)





def log(message):
    day = datetime.date.today()
    time = datetime.datetime.now().strftime("%X")
    with open(LOG_FILE, 'a') as f:
        f.write("{} {} | {}\n".format(day,time,message))

