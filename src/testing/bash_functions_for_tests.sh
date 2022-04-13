#!/usr/bin/env bash

# adresar na definicie testov (sem nakopiruj testy ktore chces spustit, ja ich budem spustat)
# TESTS_DEF_DIR = /opt/tests/

# adresar na vysledky testov (sem budem ukladat vysledky testov pre studenta)
# RESULTS_DIR = /opt/results/

# adresar s riesenim (sem nakopiruj studentske riesenie, ja ho budem testovat)
# SOLUTION_DIR = /opt/sut/

# subor/skript ktory bude spustat tvoje testy
# TEST_RUN = /bin/testsuite.sh


# 1. vytvorim kontajner a predpokladam ze ma presne tieto cesty: TESTS_DEF_DIR, RESULTS_DIR, SOLUTION_DIR, TESTS_RUN
# 2. do /opt/sut/ skopirujem cely login_dir
# 3. do /opt/tests/ skopirujem vsetky testy (vratane scoring)
# 4. do /bin/ skopirujem funkcie ktore mozes pouzivat v testsuite.sh a dotest.sh v testoch
# 5. spustim testsuite.sh
# 6. vysledky ukladam do /opt/results/testx/...
# 7. skopirujem vysledky z /opt/results/ do solution_dir/tests/
# 8. zabijem kontajner
# 9. vygenerujem hodnotenie


###############################################################################
#  NASTAVENI KONSTANT
###############################################################################

# *************** exportovane + zistene z proj conf **************
# TIMEOUT={env.cwd.proj.test_timeout}
# FUT={env.cwd.proj.sut_required}


# *************** exportovane + zistene zo spustenia ***************
# LOGIN={solution}
#  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!! < ---------------------------------------------------------------------------------------


# ********************** exportovane + default **********************
# TESTS_DIR=tests
# TEST_FILE=dotest.sh
# SPUSTENI=spusteni
# SCORING_FILE=scoring
# SCORING_PEDANTIC=scoring-pedantic

# HODNOCENI=hodnoceni-auto
# UHODNOCENI=hodnoceni-user



# ****************************** optional ******************************
# HODNFIRSTNLINES
# PEDANTIC
# SCORING
# DEBUG

# SANDBOXDIR
# SANDBOXLOCK
# SANDBOXUSER


# ******************* ak nie je exportovane --> error *******************
# (nemam ako zistit ci urcit by default)
# FUT


# *************** automaticky zistene + doplnene ak chyba ***************
# TESTS_DIR=

# LOGIN


# ************************* automaticky doplnene *************************
# TD=$TESTS_DIR/$TEST_NAME
# T=$LOGIN/$TESTS_DIR/$TEST_NAME
# test


###############################################################################
#  AUTOMATICKE DOPLNENI PROMENYCH
###############################################################################
# timeout pro testovany proces, lze zmenit v setup.sh nebo dotest.sh
[[ -n "$TIMEOUT" ]] || TIMEOUT=10s
[[ -n "$HODNFIRSTNLINES" ]] || HODNFIRSTNLINES=25
[[ -n "$PEDANTIC" ]] && SCORING_FILE=$SCORING_PEDANTIC
[[ -n "$SCORING" ]] && SCORING_FILE=$SCORING






# -n STR        non zero len
# -z STR        zero len



# help          <-- upravit
# on_exit
# die
# 
# 


##############################################################################
#          K O D   -   do not touch the running system
##############################################################################

#  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!! < ---------------------------------------------------------------------------------------
export LOGIN 

export login
export test

umask 0002

help(){
    cat <<EOF
syntax: `basename $0` [options] command
options:
    -t dir          set test set directory
    -l dir          set directory for test locks
    -d              set debug mode
command:
    ls              Vypise vsechny dostupne testy
    run testname    Provede test 'testname' nad aktualnim adresarem
    setup testname  Provede inicializaci testu 'testname'
    runall          Provede vsechny testy (radeji pouzij testovaci strategii)
    sum             Sestavi hodnoceni z vysledku testu do souboru $HODNOCENI
                    a vypise souhrne hodnoceni pro jednotlive testy
    clean           Vycisti aktualni adresar od spiny z testovani
EOF
}

# signal handler on INT TERM HUP
on_exit(){
    pids=`jobs -p`
    for pid in $pids; do
        kill -15 -$pid
        kill $pid
        wait $pid
    done 2>/dev/null
    exit 142
}

die(){
    echo "$@" >&2
    exit 1
}

debug(){
    [[ -n "$DEBUG" ]] && echo "$@" || true
}

type realpath &>/dev/null || die "chybi utilita realpath"

trap on_exit INT TERM HUP


###############################################################################
#  M A I N
###############################################################################

# bezproblemova lokalizace
export LC_ALL=C
export LANG=C

# prizpusob se prepinacum
[[ -n "$DEBUG" ]] && DEBUG=-d # -d is used for recursive run of $0
while getopts 't:l:d' c; do
    case $c in
        d) export DEBUG=-d;; # -d is used for recursive run of $0
        t) export SANDBOXDIR=$OPTARG;;
        l) export SANDBOXLOCK=$OPTARG;;
    esac
done
shift $((OPTIND-1))


# vytvor alias timeout na program s absolutni cestou (kvuli ceste na wrappery)
# pokud timeout neexistuje, potom ho nepouzivej
if [[ -x "`type -p timeout 2>/dev/null`" ]]; then
    if egrep -q '(Fedora|Debian|Ubuntu|CentOS)' /etc/issue /etc/os-release 2>/dev/null; then
        alias timeout='/usr/bin/timeout -s KILL'
    else
        alias timeout=`type -p timeout`
    fi
else
    echo "varovani: chybi timeout, nainstaluj timeout nebo coreutils" >&2
    timeout() { shift; "$@"; }
fi


############# AUTOMATICKE NASTAVENI PROMENTYCH #############

# automaticka detekce adresare testu (proj/tests/src/$(realpath $0))
if [[ -z "$TESTSDIR" ]]; then
    TESTSDIR=$(dirname $(dirname $(realpath $0)))
fi

# fronta a zamek pro vzajemne vylouceni testu
if [[ -n "$SANDBOXLOCK" ]]; then
    LOCKDIR=$SANDBOXLOCK
else
    LOCKDIR=$TESTSDIR/locks
fi

# nacti hodnoceni
if [[ -f $TESTSDIR/$SCORING_FILE ]]; then
    . $TESTSDIR/$SCORING_FILE
else
    die "Nemohu najit soubor s ohodnocenim $TESTSDIR/$SCORING_FILE"
fi

if [[ -z $TEST_FILE]]; then
    die "Neni nastavena promenna TEST_FILE"
fi

# ziskani jmen vsech testu
tests=`ls $TESTSDIR | 
    while read f; do [ -f "$TESTSDIR/$f/$TEST_FILE" ] && echo "$f"; done`


############# AUTOMATICKA DETEKCE PROMENTYCH #############


#  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!! < ---------------------------------------------------------------------------------------
# if [[ -z $LOGIN]]; then
    # die "Neni nastavena promenna LOGIN"
# fi

# test, pokud jsme v adresari s nazvem nejakeho studentskeho loginu
in_student_dir()
{
    login=$(basename `pwd`)
    [[ $login =~ ^x[a-z][a-z][a-z][a-z][a-z0-9][a-z0-9][a-z0-9]$ ]]
}


# nastavi promennou test
check_testreq()
{
    test="$1"
    if [[ -z "$test" ]] || ! grep -q "$test" <<<"$tests"; then
        die "chyba: neznamy test: $test" \
            $'\n'"pricina: byly nalezeny pouze tyto testy:"$'\n' $tests
    fi
}


# nastavi promenne T, TD podle testovaciho pripadu
prepare_test()
{
    if [[ -d "$SANDBOXDIR" ]]; then
        T=$(realpath $SANDBOXDIR)/$TESTSDIR/$test/$login
        # T=$(realpath $SANDBOXDIR)/$test/$login
    else
        T=$(realpath .)/$TESTSDIR/$test
        [[ -n "$SANDBOXUSER" ]] &&
            die "Neco je spatne. Je nastaven SANDBOXUSER=$SANDBOXUSER, ale $SANDBOXDIR pry neni dostupy..."
    fi
    TD=$TESTSDIR/$test
    mkdir -p $T || die "nepovedlo se vytvorit adresar pro test '$T'"

    # override nastaveni (napr. promenna FUT)
    if [[ -f "$TD/setup.sh" ]]; then
        . $TD/setup.sh
    fi

    if [[ -z "$SANDBOXDIR" ]]; then
        [[ -n "$FUT" ]] || die "neni nastavena promenna FUT (ve scoring)"
        cp $FUT $T || die "nepodarilo se zkopirovat '$FUT' do '$T'"
    fi
    set +x
}




# podle parametru delej, co mas
cmd="$1"
shift
case "$cmd" in
    help) help; exit 0;;
    ls) echo "$tests";;
    run|setup)
        debug "env: user=$(id -un), DEBUG=$DEBUG, SANDBOXDIR=$SANDBOXDIR, SANDBOXLOCK=$SANDBOXLOCK"
        [[ "$cmd" = setup ]] && SETUPONLY=yes
        # nastavit promennou login
        in_student_dir
        #  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!! < ---------------------------------------------------------------------------------------

        # nastavit jmeno testu a zkontrolovat jeho spravnost
        check_testreq "$1" || die "spatne jmeno testu $1"

        if [[ -n "$SANDBOXUSER" ]] && [[ "$SANDBOXUSER" != `id -un` ]]; then
            # nastavit promenne T, TD
            debug "nastavuji promenne T a TD"
            prepare_test

            debug "T=$T, TD=$TD"
            # pripravit soubory v sandboxu
            debug "pripravuji soubory v sandboxu"
            prepare_sandbox
            oldPWD=`pwd`
            cd "$T" || die "chyba: nelze nastavit aktualni adresar $T"
            #echo "Spoustim $test pod $SANDBOXUSER"
            debug "spoustim sebe pres sudo"
            sudo -u $SANDBOXUSER \
                $TESTSDIR/tst -t $SANDBOXDIR -l $SANDBOXLOCK $DEBUG $cmd "$@"
            if [[ -z "$SETUPONLY" ]]; then
                cd "$oldPWD"
                get_results # zkopirovat vysledek ze sandboxu

            fi
        else
            shift
            debug "spoustim test: `id`"
            tst_run "$@"
        fi
        debug ""
        ;;
    run_concurrently)
        maxtasks=`get_maxtasks`
        # hack pro maxtasks=1, aby to nezmrzlo,
        # protoze muze prijit SIGCHLD uprostred `jobs -p|wc -l` subshellu
        if [[ $maxtasks -eq 1 ]]; then
            while read task; do
                $0 run $task
            done
        else
            while read task; do
                active_tasks=`jobs -p|wc -l`
                while [ $active_tasks -ge $maxtasks ]; do
                    sleep 0.01
                    active_tasks=`jobs -p|wc -l`
                done
                $0 run $task &
            done
            while ! wait `jobs -p`; do true; done
        fi
        ;;
    sanitize) tst_sanitize;;
    sum) tst_sum;;
    clean) tst_clean;;
    student) in_student_dir;;
    *) help;;
esac
