import os
import subprocess

from pathlib import Path


from utils.logger import *
from utils.loading import *

from modules.environment import BASH_CMD, BASH_EXE


SRC_BASH_FILE = os.path.join(Path(__file__), 'bash_functions_for_tests.sh')
DST_BASH_FILE = os.path.join('bin', 'tst') # proj_dir/tests_dir/DST_BASH_FILE



"""
============ tests_dir/bin/tst.sh ============ B A S H
<--- dotest.sh
* run_test      - spustenie testu (sut [parametre] < vstup > vystup)
* add_tag       - pridat komentar k hodnoteniu

=============== testing/tst.py =============== P Y T H O N
<--- testsuite.sh + menu
* tst run       - spustenie testu (dotest.sh)
* tst clean     - cistenie po teste
* tst sum       - vypocet sumy

"""



"""
PROJDIR=$(realpath ../..)
TESTSDIR=$PROJDIR/tests
if [ -f $PROJDIR/sandbox.config ]; then
    . $PROJDIR/sandbox.config
fi
export PATH=$PROJDIR/bin:$PATH
export SANDBOXUSER
export SANDBOXDIR
export SANDBOXLOCK
export TESTSDIR
if [ -d "$TESTSDIR" ]; then
    $TESTSDIR/testsuite "$@"
else
    echo "chyba: nelze spustit testovaci sadu" >&2
    echo "pricina: spatne nastavena promenna TESTSDIR=$TESTSDIR" >&2
    echo "reseni: je nainstalovana testovaci sada? viz install.sh" >&2
    exit 1
fi

vars = f"PROJDIR={proj_dir}; TESTSDIR={tests_dir};"

src_dir = "/home/naty/MIT/DP/src"

export PATH={src_dir}:$PATH
export TESTSDIR
if [ -d "$TESTSDIR" ]; then
    $TESTSDIR/testsuite.sh "$@"

"""

def check_bash_functions_for_testing(proj_dir):
    tests_dir = os.path.join(proj_dir, TESTS_DIR)
    bash_file = os.path.join(tests_dir, DST_BASH_FILE)
    bash_file_exists = False
    if os.path.exists(bash_file):
        bash_file_exists = True
    else:
        try:
            if os.path.exists(SRC_BASH_FILE):
                shutil.copyfile(SRC_BASH_FILE, bash_file)
                bash_file_exists = True
        except Exception as err:
            log("copy bash functions | "+str(err))
    return bash_file_exists


def run_testsuite(stdscr, env, solution_dir):
    # nastav izolovane prostredie (TODO)
    pass

    # skontroluj ci su nakopirovane bash funkcie v tests_dir (ak nie, nakopiruj ich do tests_dir/DST_BASH_FILE)
    bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)


    # spristupni bash funkcie (export PATH=$TESTSDIR/bin:$PATH)


    # skontroluj ci je implementovany testsuite (tests_dir/TESTSUITE_FILE) a ma spravne nastavene prava

    # spusti testsuite (execute sh script)


    try:
        proj_dir = env.cwd.proj.path
        tests_dir = os.path.join(proj_dir, TESTS_DIR)
        scoring_file = os.path.join(tests_dir, SCORING_FILE)
        testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)

        # old_dir = env.cwd.path

        t_script = os.path.join(tests_dir, 'src', 't')
        # os.chdir(os.path.join(env.cwd.path, solution_dir))

        command = f"cd {solution_dir}; {t_script}\n"

        env.bash_active = True
        env.bash_function = BASH_CMD
        env.bash_cmd = command
        return env

        # process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        # process.communicate

        # log(str(output))
        # log(str(error))

        # NOPAR=y ../../bin/t
        # echo ====================================
        # grep -m1 "^[0-9].*:celkem" hodnoceni-auto
        # echo Stiskni enter...; read

        # os.chdir(old_dir)

    except Exception as err:
        log(str(err))

