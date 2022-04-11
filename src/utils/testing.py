import os
import subprocess

from pathlib import Path


from utils.logger import *
from utils.loading import *



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
export PATH=/home/naty/MIT/DP/src:$PATH
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
"""

def run_testsuite(env, solution_dir):
    # nastav izolovane prostredie (TODO)
    pass

    # skontroluj ci su nakopirovane bash funkcie v tests_dir (ak nie, nakopiruj ich do tests_dir/DST_BASH_FILE)

    # spristupni bash funkcie (export PATH=$TESTSDIR/bin:$PATH)

    # skontroluj ci je implementovany testsuite (tests_dir/TESTSUITE_FILE) a ma spravne nastavene prava

    # spusti testsuite (execute sh script)

    try:
        tests_dir = os.path.join(env.cwd.proj.path, TESTS_DIR)
        scoring_file = os.path.join(tests_dir, SCORING_FILE)
        testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)

        old_dir = env.cwd.path
        t_script = os.path.join(tests_dir, 'src', 't')
        os.chdir(os.path.join(env.cwd.path, solution_dir))

        command = f"{t_script}"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        process.communicate
        # log(str(output))
        # log(str(error))

        # NOPAR=y ../../bin/t
        # echo ====================================
        # grep -m1 "^[0-9].*:celkem" hodnoceni-auto
        # echo Stiskni enter...; read

        os.chdir(old_dir)

    except Exception as err:
        log(str(err))

