#!/usr/bin/env bash


# check_testreq         <-- upravit
# prepare_test          <-- upravit
# prepare_sandbox
# get_results           <-- upravit
# lock_test
# unlock_test
# comment                   ???
# tst_run_on_exit           ???
# tst_run_txt_filter        ???
# tst_run               <-- upravit
# score_to_points       <-- upravit
# tst_sanitize              ???
# tst_sum               <-- upravit
# in_student_dir        <-- upravit
# tst_clean             <-- upravit
# get_processors
# get_maxtasks
#  
# 



##############################################################################
# PRIVATE funkce
##############################################################################



# pripravi soubory v sandboxu, nahraje tam testovane soubory
prepare_sandbox()
{
    [[ "$T" =~ "*$SANDBOXUSER*" ]] && rm -rf "$T" 2>/dev/null
    mkdir -p "$T" || die "chyba: nelze vytvorit $T"
    chgrp $SANDBOXUSER "$T" "$T/.." ||
        die "Je $T pristupne pro zmenu prav na $SANDBOXUSER?"
    chmod 2775 "$T" "$T/.." ||
        die "Jsou $T a $T/.. pristupne pro zmenu modu na 2775?"
    cp $FUT $T/ 2>/dev/null
    oldPWD=`pwd`
    cd $T
    chmod g+w $FUT 2>/dev/null || die "Je $FUT pristupne?"
    chgrp $SANDBOXUSER $FUT 2>/dev/null ||
        die "Je $FUT pristupne. Lze zmenit skupinu na $SANDBOXUSER?"
    cd $oldPWD
}

# umozni zkopirovat vysledky z T do adresare studenta
get_results()
{
    if [[ -n "$SANDBOXDIR" ]]; then
        mkdir $test/ 2>/dev/null
        cp -a $T/* $test/ 2>/dev/null ||
            echo "$failure:$test: skript smazal test" >$test/$HODNOCENI
        cd $test
        rm $FUT 2>/dev/null
        cd ..
        rm -rf "$T" 2>/dev/null
    fi
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


# zakomentuje vstup pro hodnoceni
comment()
{
    sed 's/^/# /'
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
    . $TD/dotest.sh "$@" >$HODNOCENI 2>&1 60>&1
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
    san_dir3="/.sanitized."
    [[ -n "$PROJECT" ]] && san_dir1=$PROJECT
    [[ -n "$TESTSDIR" ]] && san_dir2=$(dirname $TESTSDIR)
    [[ -n "$SANDBOXDIR" ]] && san_dir3=$SANDBOXDIR
#    if [[ -z "$PROJECT" ]]; then
#        if [[ -z "$TESTSDIR" ]]; then
#            echo "promenna PROJECT ani PROJDIR nenastavena" >&2
#            return 1
#        else
#            san_dir1=$(realpath ../..)
#            san_dir2=$TESTSDIR
#            san_dir3=$SANDBOXDIR
#        fi
#    else
#        echo "PROJECT=$PROJECT"
#        eval san_dir1=\$$PROJECT/odevzdane
#        eval san_dir2=\$$PROJECT
#        eval san_dir3=\$$TESTSDIR
#    fi
#    [[ -z "$san_dir3" ]] && san_dir3=^/.sanitized.
    eretests="(`echo "$tests"|tr '\n' '|'|sed 's/|$//'`)"
    find . -type f -exec sed -i -r "
s#$san_dir1#/.sanitized.#g
s#$san_dir2/odevzdane#/.sanitized.#g
s#$san_dir2#/.sanitized.#g
s#$san_dir3#/.sanitized.#g
s#/.sanitized./$eretests/$login#/.sanitized.#g
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


