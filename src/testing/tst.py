#!/usr/bin/env python3

import os

# spustitelny skript
# ponuka funkcie pre testsuite.sh
# pouziva sa s argumentami: run, clean, sum

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


def tst_run():
    pass


def tst_clean():
    pass


def tst_sum():
    pass



if __name__ == "__main__":
    pass

    # sprasuj argumenty

    # podla argumentu zavolaj funkciu

