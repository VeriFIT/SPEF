#!/usr/bin/env bash

# 1. vytvorim kontajner a predpokladam ze ma presne tieto cesty: TESTS_DEF_DIR, RESULTS_DIR, SOLUTION_DIR, TESTS_RUN
# 2. do /opt/sut/ skopirujem cely login_dir
# 3. do /opt/tests/ skopirujem vsetky testy (vratane scoring)
# 4. do /bin/ skopirujem funkcie ktore mozes pouzivat v testsuite.sh a dotest.sh v testoch
# 5. spustim testsuite.sh
# 6. vysledky ukladam do /opt/results/testx/...
# 7. skopirujem vysledky z /opt/results/ do solution_dir/tests/
# 8. zabijem kontajner
# 9. vygenerujem hodnotenie



# TESTS_DIR=tests
# TEST_FILE=dotest.sh
# SPUSTENI=spusteni
# SCORING_FILE=scoring
# SCORING_PEDANTIC=scoring-pedantic

# HODNOCENI=hodnoceni-auto
# UHODNOCENI=hodnoceni-user


##############################################################################
#  K O D
##############################################################################

export test

umask 0002

help()
{
    cat <<EOF
syntax: `basename $0` command
command:
    ls              Return list of implemented test names
    run testname    Execute test witn 'testname' under current directory (expecting cwd=sut dir)
    sum             Evaluate total score from executed tests (according to defined equation from 'sum' file)
                    + add tag with name 'score' and its value as argument
    report          Generate report from tests
    clean           Remove outputs from test in current directory (clean test results)
    student         Return true if current directory is solution dir (student dir)
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

type realpath &>/dev/null || die "chybi utilita realpath"
trap on_exit INT TERM HUP


###############################################################################
#  M A I N
###############################################################################

# bezproblemova lokalizace
export LC_ALL=C
export LANG=C

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


############# NASTAVENI PROMENTYCH #############

# automaticka detekce adresare testu (proj/tests/src/$(realpath $0))
if [[ -z "$TESTSDIR" ]]; then
    TESTSDIR=$(dirname $(dirname $(realpath $0)))
fi

# default values
[[ -n "$TIMEOUT" ]] || TIMEOUT=10s
[[ -n "$HODNFIRSTNLINES" ]] || HODNFIRSTNLINES=25
[[ -n "$SCORING" ]] || SCORING=scoring
[[ -n "$TEST_FILE" ]] || TEST_FILE=dotest.sh

# fronta a zamek pro vzajemne vylouceni testu
LOCKDIR=$TESTSDIR/locks

# nacti hodnoceni
if [[ -f $TESTSDIR/$SCORING ]]; then
    . $TESTSDIR/$SCORING
else
    die "Nemohu najit soubor s ohodnocenim $TESTSDIR/$SCORING"
fi

if [[ -z $TEST_FILE]]; then
    die "Neni nastavena promenna TEST_FILE"
fi

if [[ -z "$LOGIN" ]]; then
    die "Neni nastavena promenna LOGIN"
fi

if [[ -z "$FUT" ]]; then
    die "Neni nastavena promenna FUT"
fi


############# PRIVATNI FUNKCE #############

# test, pokud jsme v adresari s nazvem nejakeho studentskeho loginu
in_student_dir()
{
    [[ "$LOGIN"=="$(basename `pwd`)" ]]
}


# nastavi promennou test
check_testreq() {
    test="$1"
    if [[ -z "$test" ]] || ! grep -q "$test" <<<"$tests"; then
        die "chyba: neznamy test: $test" \
            $'\n'"pricina: byly nalezeny pouze tyto testy:"$'\n' $tests
    fi
}


# nastavi promenne T, TD podle testovaciho pripadu
prepare_test() {
    T=$(realpath .)/$TESTSDIR/$test
    TD=$TESTSDIR/$test
    mkdir -p $T || die "nepovedlo se vytvorit adresar pro test '$T'"

    # override nastaveni (napr. promenna FUT)
    if [[ -f "$TD/setup.sh" ]]; then
        . $TD/setup.sh
    fi

    cp $FUT $T || die "nepodarilo se zkopirovat '$FUT' do '$T'"
    set +x
}


# zamkni/odemkni test
lock_test()
{
    # FIXME: poor sync, non-atomic
    lname=`basename $1`
    lockname=$LOCKDIR/"$lname"
    [[ -d $LOCKDIR ]] || mkdir -p $LOCKDIR &>/dev/null
    while :; do 
        if [[ -f $lockname ]]; then
            pid=`cat $lockname`
            if [[ -d /proc/$pid ]]; then
                echo "Test $lname se jiz provadi (pid $pid), cekam..." >&2
                sleep 1
                continue
            fi
        fi
        break
    done
    echo $$ >$lockname
    unset lname
}

unlock_test()
{
    rm $lockname 2>/dev/null
}


# signal handler pro testovani
tst_run_on_exit()
{
    wrappers_off
    unlock_test
    exit 142
#    kill -15 `jobs -p`
#    pids=`jobs -p`
#    for pid in $pids; do
#        kill -15 -$pid
#        kill $pid
#        wait $pid
#    done 2>/dev/null
}

# ziskej pocet procesoru na masine
get_processors()
{
    case `uname` in
        Linux) grep ^processor /proc/cpuinfo|wc -l;;
        FreeBSD) sysctl -a|grep 'hw.ncpu'|cut -d: -f2;;
        SunOS) psrinfo -p;;
    esac
}

get_maxtasks()
{
    [ "$MAXTASKS" ] && { echo $MAXTASKS; return; }
    local maxcpu=`get_processors`
    if [[ $maxcpu -le 2 ]]; then
        # experimentalne zmereno na 1,2,4,8 a 16 cpu s hyperthreadingem
        echo $((maxcpu*2))
    else
        echo $((maxcpu+maxcpu/2))
    fi
}


############# TODO: UPRAVIT ############# !!!!!!!!!!!!!!1



# vzor dotest.sh pro testovani textovych filtru
# v dotest.sh pak pouze staci pouze nastavit promenne:
#   filter=extregexp   nenulovy=ze je potreba provest tuto funkci
#                   extregexp, ktere radky stdout a stderr se maji porovnavat 
#                   filter=^ pokud nic nefiltrovat
#   cmd="../prikaz co spustit"
#   msg="kratky popis testu"
#   diff=y      # pri neshode s vysledky (stdout.ref a stderr.ref) tisk rozdilu
tst_run_txt_filter()
{
    [[ -x "`type -p "$2" 2>/dev/null`" ]] || return
    filter="$1"
    shift
    cp $TD/stdin .
    run_test "$@"
    [[ $? -ge 124 ]] && return
    if [[ "$filter" ]]; then
        echo "stdout a stderr filtrovano na $filter" >>$SPUSTENI
        egrep -e "$filter" <stdout >stdout.$$
        egrep -e "$filter" <stderr >stderr.$$
        mv stdout.$$ stdout
        mv stderr.$$ stderr
    fi
    cp $TD/stdout.ref $TD/stderr.ref .
    local d
    if d=`diffall`; then
        echo "$success:ok:$msg"
    else
        if [[ "$diff" = y ]]; then
            echo "$failure:chyba:$msg"
            echo "$d"
        else
            echo "$failure:chyba:$msg viz $test/stdouterr.diff"
            echo "$d" >stdouterr.diff
        fi
    fi
}



# chovani pri spusteni s parametry: run test_name [args]
tst_run()
{
    # signal handler pro testy
    trap tst_run_on_exit INT TERM HUP
    # priprava
    lock_test `pwd`.$test
    prepare_test
    echo "Spoustim test $test ... (`id -un`)" >&2
    oldPWD=$PWD
    cd $T
    # nastaveni scoring promennych
    success=`set | grep ^${test}_ok=`
    success=${success#*=}
    [[ -z "$success" ]] && success=1
    failure=`set | grep ^${test}_fail=`
    failure=${failure#*=}
    [[ -z "$failure" ]] && failure=0
    # provedeni testu
    unset filter cmd msg diff   # pokud se jedna jen o textovy filtr

    # $TEST_FILE = dotest.sh
    # . tests_dir/bin/tst.sh # <-- include tests_dir/bin/tst.sh, potom dotest.sh moze pouzivat funkcie ktore su definovane v tests_dir/bin/tst.sh
    . $TD/$TEST_FILE "$@" >$HODNOCENI 2>&1 60>&1
    wrappers_off
    [[ "$filter" ]] &&
        tst_run_txt_filter "$filter" $cmd >$HODNOCENI 2>&1 60>&1
    # uklid a nastaveni prav
    if [[ -n "$SANDBOXDIR" ]]; then
        chmod -R g+rwX $T 2>/dev/null
    fi
    cd $oldPWD
    unlock_test
    unset success
    unset failure
    # zpet implicitni signal handler
    trap - INT TERM HUP
#    trap on_exit INT TERM HUP
}

# Prepocet score na body, vyuziva se pomer MAXPOINTS a MAXSCORE. Pokud testy
# mohou dat hodnoceni v souctu vetsi nez MAXPOINTS (toto je detekovano definici
# promenne MAXSCORE), potom se pouzije tato funkce: prepocitava score na stdin
# na body na stdout.
score_to_points()
{
    awk -v MAXSCORE=$MAXSCORE -v MAXPOINTS=$MAXPOINTS '{
        score=$1
        if (score < 0)
            score = 0
        if (score > MAXSCORE)
            score = MAXSCORE
        body = score*1.0 / MAXSCORE * MAXPOINTS
        if (body > 0 && body < 1)
            body = 1
        print int(body+0.5)
    }'
}

# ve vsech souborech rekurzivne nahradi kazdy vyskyt retezce z promenne
# $IOS_.._. (jmeno promenne zjisti z $PROJECT) a retezce "$IOS.._./odevzdane" a
# nahradi ho: "/.sanitized./"
tst_sanitize()
{
    if ! in_student_dir; then
        echo "nejsme v adresari studenta! nic nenahrazuji" >&2
        return 1
    fi
    san_dir1="/.sanitized."
    san_dir2="/.sanitized."
    [[ -n "$PROJECT" ]] && san_dir1=$PROJECT
    [[ -n "$TESTSDIR" ]] && san_dir2=$(dirname $TESTSDIR)
    eretests="(`echo "$tests"|tr '\n' '|'|sed 's/|$//'`)"
    find . -type f -exec sed -i -r "
s#$san_dir1#/.sanitized.#g
s#$san_dir2#/.sanitized.#g
s#/.sanitized./$eretests/$LOGIN#/.sanitized.#g
s#/.sanitized./$eretests#/.sanitized.#g" {} \;
}


# chovani pri spusteni s parametem: sum
tst_sum()
{
    # srandicky s barvickama
    if [[ -t 1 ]]; then
        c_red=`tput setaf 1`
        c_normal=`tput sgr0`
    fi 
    # uzivatelem definovane hodnoceni uplne nahoru
    if [[ -f $UHODNOCENI ]]; then
        echo "#-- rucni uprava hodnoceni ----------------------------"
        cat $UHODNOCENI
    fi >$HODNOCENI
    # pod to hodnoceni z testovani
    echo "#-- automaticke hodnoceni -----------------------------" >>$HODNOCENI
    hodnoceni=
    for tname in $tests; do
        if [[ -f "$tname/$HODNOCENI" ]]; then
            if [[ `wc -l <$tname/$HODNOCENI` -gt $HODNFIRSTNLINES ]]; then
                cat $tname/$HODNOCENI | head -n $HODNFIRSTNLINES
                echo "# Vypis byl zkracen, cely text viz $tname/$HODNOCENI"
            else
                cat $tname/$HODNOCENI
            fi
            bodytest=`grep -v ^# $tname/$HODNOCENI |
                awk -F: '{sum+=$1}END{print sum}'`
                #awk -F: '{sum+=$1}END{print int(sum+.5)}'`
            if [[ "$bodytest" -le 0 ]]; then
                hodnoceni="$hodnoceni
$c_red$tname=$bodytest$c_normal"
            else
                hodnoceni="$hodnoceni
$tname=$bodytest"
            fi
        fi
    done >>$HODNOCENI
    echo "#------------------------------------------------------" >>$HODNOCENI
#    sum=`grep -v ^# $HODNOCENI | awk -F: '{sum+=$1}
#        END{if (int(sum)!=sum) print int(sum+.5); else print sum}'`
#    sum=`grep -v ^# $HODNOCENI|awk -F: '{sum+=$1}END{print int(sum+.5)}'`
    score=`grep -v ^# $HODNOCENI|awk -F: '{sum+=$1}END{print sum}'`
    if [[ -z "$MAXSCORE" ]]; then
        echo "$score:celkem bodu za projekt" >>$HODNOCENI
        sed -i "1i$score:celkem bodu za projekt" $HODNOCENI
    else
        echo "$score:celkove score (max pro hodnoceni $MAXSCORE)" >>$HODNOCENI
        bodu=`score_to_points <<<$score`
#        [[ $sum -gt $MAXPOINTS ]] && sum=$MAXPOINTS
        echo "$bodu:celkem bodu za projekt" >>$HODNOCENI
        sed -i "1i$bodu:celkem bodu za projekt" $HODNOCENI
    fi
    echo "$hodnoceni" | sed -n '2,$p'
}




# chovani pri spusteni s parametrem: clean
tst_clean()
{
    echo Mazu vysledky testu >&2
    # bezpecnostni mechanismus, at nejsme v adresari testu
    if [ $TESTSDIR = $(realpath $(pwd)) ]; then
        echo "jsme v adresari s testy! nic nemazu" >&2
        return 1
    fi
    # bezpecnostni mechanismus (jsme v login adresari?)
    if ! in_student_dir; then
        echo "nejsme v adresari studenta! nic nemazu" >&2
        return 1
    fi
    for t in $tests; do
        [ -d $t ] && chmod -R +w $t && rm -r $t
    done
    rm -f $HODNOCENI hodnoceni.tgz 2>/dev/null
}





###############################################################################
#  M A I N
###############################################################################


# ziskani jmen vsech testu
tests=`ls $TESTSDIR | 
    while read f; do [ -f "$TESTSDIR/$f/$TEST_FILE" ] && echo "$f"; done`


# podle parametru delej, co mas
cmd="$1"
shift
case "$cmd" in
    help) help; exit 0;;
    ls) echo "$tests";;
    run)
        in_student_dir
        # nastavit jmeno testu a zkontrolovat jeho spravnost
        check_testreq "$1" || die "spatne jmeno testu $1"
        # nastavit promenne T, TD
        prepare_test
        oldPWD=`pwd`
        cd "$T" || die "chyba: nelze nastavit aktualni adresar $T"
        tst_run "$@"
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
