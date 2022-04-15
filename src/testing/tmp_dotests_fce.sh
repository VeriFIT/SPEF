#!/usr/bin/env bash


# wrappers_on           ???
# wrappers_off          ???
# run_test          <-- upravit
# sort_out
# sortu_out
# nwdiff
# diffni
# diffall
# in_set
# diffdir
# diffdirboth
# auto_report       <-- upravit
# asserterror       <-- upravit
# 
# 



##############################################################################
# PUBLIC funkce (pro dotest.sh)
##############################################################################

# wrappers_on/off zapne/vypne wrappery pro shell utility.
# pouziti: wrappers_on [adresar s wrappery] nebo
#          wrappers_off
# on: nastavi promennou PATH s nastavenymi wrappery na prvni misto, vytvori
#     soubor $T/cmds.log a exportuje ho do promenne WRAPPERS_LOG
# off: obnovi PATH
# $1 = EXPORTED_VAR1=value1
# $2 = EXPORTED_VAR2=value2
# $3 = ...
wrappers_on()
{
    wrappers="$TESTSDIR/wrappers"
    if [ -d "$1" ]; then
        wrappers="$1"
        shift
    fi
    export WRAPPERS_LOG=$T/cmds.log
    true >$WRAPPERS_LOG
    oldpath=$PATH
    export PATH=$wrappers:$PATH
    for exported_item in "$@"; do
        export $exported_item
    done
    unset exported
    unset wrappers
}
wrappers_off()
{
    [[ -n "$oldpath" ]] && export PATH=$oldpath
    unset oldpath
}

# wrapper pro spusteni testovaneho programu,
# jmeno programu s jeho parametry budou jako parametry teto funkce
# POUZIVANO TESTEM (tj. je to volano skriptem `dotest.sh')
# (pozn. mel by byt pripraveny na spusteni mezi wrappers_on a wrappers_off)
run_test()
{
    # pokud existuje referencni stdin, zkopiruj ho do testu
    [[ -f $TD/stdin.ref ]] && cp $TD/stdin.ref $T/stdin
    # pokud neexistuje (ani pripraveny dotest.sh),
    # priprav prazdny std. vstup (at nam nesaha na terminal)
    [[ -f $T/stdin ]] || touch $T/stdin
    ( for arg in "$@"; do
        if [[ "$arg" =~ ^[-a-zA-Z0-9_+=.,/@#%^]+$ ]]; then
            /usr/bin/printf "%s " "$arg"
        else
            arg=${arg//\'/\'\\\'\'}
            /usr/bin/printf "'%s' " "$arg"
        fi
    done
    printf '<stdin >>stdout 2>>stderr; echo $? >>errcode\n'
    ) >>$T/$SPUSTENI
    # pokud jsme meli pouze pripravit test, pak koncime
    if [[ -n "$SETUPONLY" ]]; then
        unlock_test
        exit 0
    fi
    # spust to, omez ho casem
    # assert: timeout je alias na absolutni cestu k timeoutu
    timeout $TIMEOUT "$@" <$T/stdin >>$T/stdout 2>>$T/stderr
    status=$?
    # obnov puvodni cestu
    if [[ -n "$WRAPPERS" ]]; then
        export PATH=$oldpath
        unset oldpath
    fi
    # 124 nebo 137, zalezi na verzi timeout
    timeout=$TIMEOUT
    [[ -n "$EXTTIMEOUT" ]] && 
        timeout="$TIMEOUT (jiz prodlouzeny - neco je spatne)"
    if [[ $status -ge 124 ]]; then
        {
        echo "$failure:$test: chyba pri spusteni, mozne priciny:"
        echo ":chybny soubor, timeout $timeout nebo limit velikosti souboru"
        } >&60
        echo timeout $timeout >$T/timeout
    else
        echo $status >>$T/errcode
    fi
    return $status
}

# Seradi soubor 'stdout' in-situ.
sort_out()
{
    sort <stdout >stdout.sorted &&
        mv stdout.sorted stdout
}

# Seradi soubor 'stdout' in-situ a unikatne.
sortu_out()
{
    sort -u <stdout >stdout.sorted &&
        mv stdout.sorted stdout
}

# (no whitespace diff) diffne soubory, pricemz ignoruje veskere bile znaky
# vcetne konce radku pokud se lisi, vrati vystup normalniho diffu. V pripade
# nenuloveho PEDANTIC porovna bajt s bajtem.
nwdiff()
{
    if [[ -n "$PEDANTIC" ]]; then
        diff -u "$1" "$2"
    else
        f1=`mktemp /tmp/tst.XXXXXX`
        f2=`mktemp /tmp/tst.XXXXXX`
        tr -d ' \t\n\r' <"$1" >$f1
        tr -d ' \t\n\r' <"$2" >$f2
        ok=
        if ! cmp -s $f1 $f2; then
            diff -Bbwu "$1" "$2" | 
                sed '1,2s#\([-+][-+][-+] .*\)\t[-0-9:.+ ]*#\1#'
            ok=no
        fi
        rm -f $f1 $f2
        [[ -z "$ok" ]]
    fi
}

# diffne stdout a stdout.ref, vrati lehce naformatovany diff
# a FALSE, pokud se najde nejaky rozdil
# POUZIVANO TESTEM dotest.sh timto zpusobem:
#    if d=`diffni`; then echo OK; else echo FAILED; echo "$d"; fi
# pripadne: diffni [volby] [referenceni_soubor skutecny_soubor]
# volby:
#   -s  provede diffni nad soubory, jejichz obsah nejprve seradi (provede
#       kopii souboru s priponou .sorted) nebo
#   -u  provede diffni nad unikatne serazenymi soubory (obdoba -s, ale serazeni
#       bude unikatni -- viz sort -u, vytvori kopii s priponou .usorted)
diffni()
{
    ref=stdout.ref
    dst=stdout
    sorted=
    if [[ "x$1" = x-s ]]; then
        sorted=sorted
        sortargs=
        shift
    elif [[ "x$1" = x-u ]]; then
        sorted=usorted
        sortargs=-u
        shift
    fi
    [[ -n "$1" ]] && ref="$1"
    [[ -n "$2" ]] && dst="$2"
    if ! [[ -f "$dst" ]]; then
        echo "# $dst chybi (byl smazan?)"
        return 1
    fi
    if [[ -n "$sorted" ]]; then
        sort $sortargs <$ref >$ref.$sorted
        ref=$ref.$sorted
        sort $sortargs <$dst >$dst.$sorted
        dst=$dst.$sorted
    fi
    if ! d=`nwdiff $ref $dst`; then
        [[ -f $SPUSTENI ]] && sed 's/^/# /' $SPUSTENI
        echo "# diff -u $ref $dst"
        echo "$d" | sed 's/^/#   /'
        return 1
    fi
}

# diffne stdout s stdout.ref, a stderr s stderr.ref
# vrati lehce naformatovany diff a FALSE, pokud se najde nejaky rozdil
# POUZIVANO TESTEM dotest.sh timto zpusobem:
#    if d=`diffall`; then echo OK; else echo FAILED; echo "$d"; fi
diffall()
{
    if [[ -f errcode.ref ]]; then
        if ! cmp -s errcode.ref errcode; then
            errcodes=`tr '\n' , <errcode|sed 's/,$//'`
            errcodes_expected=`tr '\n' , <errcode.ref|sed 's/,$//'`
            d0="# errcode=$errcodes; ocekavan errcode=$errcodes_expected"
        else
            d0=
        fi
    fi
    diff1=true
    diff2=true
    [[ -f stdout.ref ]] && diff1="nwdiff stdout.ref stdout"
    [[ -f stderr.ref ]] && diff2="nwdiff stderr.ref stderr"
    d1=`echo "# diff -u stdout.ref stdout"; $diff1`
    r1=$?
    d2=`echo "# diff -u stderr.ref stderr"; $diff2`
    r2=$?
    if [[ -n "$d0" ]] || [[ $r1 != 0 ]] || [[ $r2 != 0 ]]; then
        if [[ -f $SPUSTENI ]]; then
            if [[ $r1 != 0 ]] || [[ $r2 != 0 ]]; then
                sed 's/^/# /' $SPUSTENI
            fi
        fi
        [[ -n "$d0" ]] && echo "$d0"
        [[ $r1 != 0 ]] && echo "$d1" | sed '2,$s/^/#   /'
        [[ $r2 != 0 ]] && echo "$d2" | sed '2,$s/^/#   /'
        return 1
    fi
    return 0
}

# vrati SUCCESS pokud item \in {i1, i2, ..., iN}
# usage: in_set item i1 i2 ... iN
in_set()
{
    item="$1"
    shift
    for i in "$@"; do
        [[ "$item" = "$i" ]] && return 0
    done
    return 1
}

# usage: diffdir [-b] referencni.dir testovany.dir
# Provede diff kazdeho souboru v referencni.dir se souborem v testovany.dir.
# Soubory vyskytujici se pouze v testovany.dir ignoruje. V pripade zjisteneho
# rozdilu tiskne report a vrati FAILURE; jinak nic netiskne a vrati SUCCESS.
# Parametr:
# -b    (brief diff) tiskne jen info o rozdilu, ne cely rozdil
# note: nejsou podporovany bile znaky ve jmenech souboru a adresaru
diffdir()
{
    brief=
    if [[ "$1" = -b ]]; then
        brief=yes
        shift
    fi
    dir1="$1"
    dir2="$2"
    [[ -d "$dir1" ]] || return 1
    if ! [[ -d "$dir2" ]]; then
        echo "# $dir2 nenalezen"
        return 1
    fi
    report=
    files=`cd "$dir1"; find . -type f 2>/dev/null | sed 's/^\.\///'`
    for file in $files; do
        if ! [[ -f $dir2/$file ]]; then
            report="${report}# chybi: $dir2/$file
"
        else
            if ! d=`nwdiff $dir1/$file $dir2/$file`; then
                if [[ -n "$brief" ]]; then
                    report="${report}# lisi se: $dir1/$file a $dir2/$file
"
                else
                    d=`echo "$d"|sed 's/^/#   /'`
                    report="${report}# diff -u $dir1/$file $dir2/$file
$d
"
                fi
            fi
        fi
    done
    if [[ -n "$report" ]]; then
        echo -n "# porovnani souboru v $test s referenci
$report"
        return 1
    else
        return 0
    fi
}

# usage: diffdirboth [-b] referencni.dir testovany.dir
# Provede diff kazdeho souboru v referencni.dir se souborem v testovany.dir.  V
# pripade zjisteneho rozdilu tiskne report a vrati FAILURE; jinak nic netiskne
# a vrati SUCCESS.
# Parametr:
# -b    (brief diff) tiskne jen info o rozdilu, ne cely rozdil
# note: nejsou podporovany bile znaky ve jmenech souboru a adresaru
diffdirboth()
{
    brief=
    if [[ "x$1" = x-b ]]; then
        brief=yes
        shift
    fi
    dir1="$1"
    dir2="$2"
    [[ -d "$dir1" ]] || return 1
    if ! [[ -d "$dir2" ]]; then
        echo "# $dir2 nenalezen"
        return 1
    fi
    report=
    files=`cd "$dir1"; find . -type f 2>/dev/null | sed 's/^\.\///'`
    for file in $files; do
        if ! [[ -f $dir2/$file ]]; then
            report="${report}# chybi: $dir2/$file
"
        else
            if ! d=`nwdiff $dir1/$file $dir2/$file`; then
                if [[ -n "$brief" ]]; then
                    report="${report}# lisi se: $dir1/$file a $dir2/$file
"
                else
                    d=`echo "$d"|sed 's/^/#   /'`
                    report="${report}# diff -u $dir1/$file $dir2/$file
$d
"
                fi
            fi
        fi
    done
    files=`cd "$dir2"; find . -type f 2>/dev/null | sed 's/^\.\///'`
    for file in $files; do
        if ! [[ -f $dir1/$file ]]; then
            report="${report}# soubor navic: $dir2/$file
"
        fi
    done
    if [[ -n "$report" ]]; then
        echo -n "# porovnani souboru v $test s referenci
$report"
        return 1
    else
        return 0
    fi
}

# Vypise report o vysledku. Zamysleno pri pouziti v dotest.sh
# ...
# run_test ./SUT ...
# auto_report "brief popis testu"
#  $T = adresar testu
#  $TD = adresar s referencnimi daty
#  $success = scoring passed
#  $failure = scoring failure
#  $test = jmeno testu
#  $stdoutfilter (volitelne) = filter na stdout (napr. "sort -u")
#  $@ = zprava
auto_report()
{
    [[ -f $TD/stdout.ref ]] && cp $TD/stdout.ref $T/
    [[ -f $TD/stderr.ref ]] && cp $TD/stderr.ref $T/
    [[ -f $TD/errcode.ref ]] && cp $TD/errcode.ref $T/
    if [[ -n "$stdoutfilter" ]]; then
        cp stdout stdout.orig
        cat stdout.orig | eval $stdoutfilter >stdout
    fi
    if d=`diffall`; then
        echo "$success:ok: $@"
    else
        echo "$failure:$test: $@"
        echo "$d"
    fi
}

# Vypise report o vysledku, o kterem se ocekava nenulovy navratovy kod a
# neprazdny stderr
#   run_test ./SUT ...
#   asserterror "brief popis testu"
#  $T = adresar testu
#  $success = scoring passed
#  $failure = scoring failure
#  $test = jmeno testu
#  $@ = zprava
# V pripade nejake chyby se do zavorky za popis testu pripise zduvodneni
asserterror()
{
    [[ -s $T/stderr ]] && stderrok=e
    [[ `cat $T/errcode` -gt 0 ]] && ecodeok=c
    case $stderrok$ecodeok in
        ec) echo "$success:ok: $@";;
        c) echo "$failure:$test: $@ (chybi zprava na stderr)";;
        e) echo "$failure:$test: $@ (neni chybny navratovy kod)";;
        *) echo "$failure:$test: $@ (neni stderr a chybovy kod)";;
    esac
}



