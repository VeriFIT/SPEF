#!/usr/bin/env bash

# autor: Ales Smrcka
# uprava: Natalia Dizova


###############################################################################
#  JAK PROBIHA TEST
###############################################################################
# Musi byt nastavene promenne: TESTSDIR, login, TAG_FILE, FUT

# Pri spusteni testu z adresare se studentskym resenim ("tst run jmeno_testu",
# kde jmeno_testu je nazev adresare minimalne se souborem `dotest.sh'):
# 1. Ze souboru s hodnocenim se nactou hodnotici promenne a vsechny se
#    exportuji. Implicitne se tento soubor jmenuje $SCORING_FILE (viz nize).
#    Pokud je v promennem prostredi nastavena promenna $PEDANTIC, pak se
#    pouzije soubor $SCORING_PEDANTIC. Pokud je nastavena promenna $SCORING,
#    pak se pouzije soubor z teto promenne. Soubor s hodnocenim se ocekava v
#    adresari s testy.
# 2. Uzamkne se dany test pro daneho studenta (to kdyby sis u pripravy testu
#    neuvedomil, ze by mohly oba testy probehnout zaroven - treba pri
#    paralelnim testovani).
# 3. Nastavi se lokalizace C.
# 4. Bude nastavena promenna T s pracovnim adresarem testu (urceneho pro beh
#    jednoho testu jednoho studenta). V pripade sandboxu bude nastaven v
#    $SANDBOXDIR/xlogin_studenta.jmeno_testu. Obsah tohoto adresare bude
#    nejprve vymazan (pokud existuje) a nasledne vytvoren prazdny.
# 6. Do promenne TD se nastavi adresar definice testu - ten, ktery jsi
#    vytvoril rucne v sekci 1.2 (viz ^).
# 7. V promenne TESTSDIR bude cesta ke vsem testum (to kdybys tam mel treba
#    dummy prikazy a chtel jsi upravit PATH tak, aby se odkazovala na ne).
# 8. V aktualnim prostredi se provede `dotest.sh', jeho vystup se ulozi do
#    souboru $HODNOCENI (viz nize) v nove vytvorenem adresari $T. Skriptu
#    `dotest.sh' lze predat parametry, pokud se zadaji za jmeno testu (viz
#    1.4.c a 1.4.d). Vse, co `dotest.sh' vypise, bude ulozeno do souboru
#    $HODNOCENI v adresari testu.
# 9. Pokud se testovany program bude spoustet z `dotest.sh' pomoci funkce
#    `run_test', bude nasilne ukoncen po vyprseni doby $TIMEOUT (viz nize, lze
#    nastavit v prostredi shellu pri spusteni tohoto testovaciho prostredi).
#    Navic toto bude oznameno v souboru s hodnocenim daneho testu (viz
#    run_test).
# 10. Odemkne se test.

# Rekapitulace promennych konfigurujici chovani testu:
#    PEDANTIC - neprazdny retezec zpusobi pouziti $SCORING_PEDANTIC hodnoceni
#    SCORING  - urcuje soubor s hodnocenim (ma prioritu pred PEDANTIC)
#    TIMEOUT  - timeout (se suffixem jednotky) pro jeden test
# Promenne nastavene pro `dotest.sh':
#    TESTSDIR - adresar s testy
#    TD       - adresar s definici aktualne provadeneho testu
#    T        - vytvoreny adresar urceny pro vysledky testu


###############################################################################
#  NASTAVENI KONSTANT (pokud mozno nemenit)
###############################################################################
# Sem nastav root adresar testu (tam, kde je soubor tst a podadresare
# jednotlivych testu). Nech prazdny pro automatickou detekci (podle $0).
# Jmena adresaru testu musi splnovat omezeni pro nazvy promenne shellu, musi
# obsahovat soubory setup.sh a dotest.sh, ktere jsou timto skriptem
# includovany.
# Ocekava se, ze test bude provaden z adresare, ve kterem chceme zaznamenat
# jeho testovaci vysledky.
TESTSDIR=

# Bodovani jednotlivych casti testu je ulozeno v souboru SCORING_FILE. Tento
# soubor obsahuje prirazeni float cisel do promennych. Tyto promenne by mel
# pouzivat kazdy soubor `dotest.sh' v 
# soubor s maximalnim hodnocenim (bude hledan v $TESTSDIR)
SCORING_FILE=scoring
# pedantic varianta souboru s hodnocenim
SCORING_PEDANTIC=scoring-pedantic

# timeout pro testovany proces, lze zmenit v setup.sh nebo dotest.sh
[[ -n "$TIMEOUT" ]] || TIMEOUT=10s

# soubor s automatickym hodnocenim
HODNOCENI=hodnoceni-auto
# soubor s rucni upravou hodnoceni od tebe (pouziva se pro: tst sum)
UHODNOCENI=hodnoceni-user

# soubor s udajem, jak byl skript/program spusten (bude v adresari testu)
SPUSTENI=spusteni

# Promenna MAXTASKS pro omezeni poctu paralelne provadenych akci.
# Pokud neni definovana nebo je praznda, jeji hodnota bude zjistena
# automaticky podle poctu procesoru.
#MAXTASKS=      # zakomentovano, aby jeji hodnotu mohl ovlivnit uzivatel

# Promenna HODNFIRSTNLINES slouzi pro maximalni pocet radku kopirovanych z
# textu vysledku jednotlivych testu do souboru s textem celkoveho hodnoceni.
[[ -n "$HODNFIRSTNLINES" ]] || HODNFIRSTNLINES=25

##############################################################################
#          K O D   -   do not touch the running system
##############################################################################

# nestaci coreutils realpath, protoze potrebujeme i pro neexistujici cesty
#realpath_wrapper() { python -c "import os; print(os.path.realpath('$12'))"; }

export test

umask 0002

help()
{
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
on_exit()
{
    pids=`jobs -p`
    for pid in $pids; do
        kill -15 -$pid
        kill $pid
        wait $pid
    done 2>/dev/null
    exit 142
}

die()
{
    echo "$@" >&2
    exit 1
}

debug()
{
    [[ -n "$DEBUG" ]] && echo "$@" || true
}

type realpath &>/dev/null || die "chybi utilita realpath"

trap on_exit INT TERM HUP


get_fce_for_dotest(){
    cat <<EOF
wrappers_on [adresar]       = zapne wrappery pro shell utility
wrappers_off                = vypne wrappery pro shell utility
run_test sut [param]        = wrapper pro spusteni testovaneho programu (sut)
sort_out                    = seradi soubor 'stdout' in-situ
sortu_out                   = seradi soubor 'stdout' in-situ a unikatne
nwdiff f1 f2                = diffne soubory, ignoruje  bile znaky vcetne konce radku
diffni [-s|-u] [ref test]   = diffne soubory (by default 'stdout' a 'stdout.ref')
diffall                     = diffne 'stdout' s 'stdout.ref', a 'stderr' s 'stderr.ref'
diffdir [-b] ref test       = diff soubory v ref/ se soubory v test/ (soubory navic ignoruje)
diffdirboth [-b] ref test   = diff soubory v ref/ se soubory v test/
auto_report "popis testu"   = vypise report o vysledku
asserterror "popis testu"   = vypise report o vysledku (ocekava nenulovy 'errcode' a 'stderr')
add_test_tag "tag" [params] = prida tag do souboru $TAGS (tagy vysledku testu)
EOF
}

if [[ "$1" == "get_fce" ]]; then
    get_fce_for_dotest; exit 0;
fi


##############################################################################
# PUBLIC funkce (pro dotest.sh)
##############################################################################


# add_test_tag "scoring_${test}" ${success} $@
# add_test_tag "scoring_${test}" ${failure} $@ ${d}
# add_test_tag "${test}_ok"

# Prida tag k vysledkom testov
# add_test_tag tag_name [args]
#  $RESULTS_DIR/$TAG_FILE = subor s tagmi
#  $success = scoring passed
#  $failure = scoring failure
#  $test = meno testu
#  $1 = meno tagu
#  $2, $3, ... = argumenty tagu
# typicke pouzitie:
#   add_test_tag "scoring_test1" "body" "popis testu" "doplnujuce info"
#   add_test_tag "test1_fail" "pricina zlyhania"
add_test_tag(){
    res="${1}:"
    shift
    if [[ -z "$@" ]]; then
        res="${res} []" >> $TAGS
    else
        for arg in "$@"; do
            if [[ -n "$arg" ]]; then
                res="${res}\n- ${arg}" >> $TAGS
            fi
        done
    fi
    printf "${res}\n" >> $TAGS
}


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

        add_test_tag "scoring_${test}" ${failure} "chyba pri spusteni"
        add_test_tag "${test}_fail" "chybny soubor, timeout ${timeout} nebo limit velikosti souboru"
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
        add_test_tag "scoring_${test}" ${success} "$@"
        add_test_tag "${test}_ok"
    else
        echo "$failure:$test: $@"
        echo "$d"
        add_test_tag "scoring_${test}" ${failure} "$@"
        add_test_tag "${test}_fail"
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
        ec) echo "$success:ok: $@"
            add_test_tag "scoring_${test}" ${success} "$@"
            add_test_tag "${test}_ok"
            ;;
        c)  echo "$failure:$test: $@ (chybi zprava na stderr)"
            add_test_tag "scoring_${test}" ${failure} "$@"
            add_test_tag "${test}_fail" "chybi zprava na stderr"
            ;;
        e)  echo "$failure:$test: $@ (neni chybny navratovy kod)"
            add_test_tag "scoring_${test}" ${failure} "$@"
            add_test_tag "${test}_fail" "chybi zprava na stderr"
            ;;
        *)  echo "$failure:$test: $@ (neni stderr a chybovy kod)"
            add_test_tag "scoring_${test}" ${failure} "$@"
            add_test_tag "${test}_fail" "neni stderr a chybovy kod"
            ;;
    esac
}

##############################################################################
# PRIVATE funkce
##############################################################################

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
        T=$(realpath $SANDBOXDIR)/$test/$login
    else
        T=$(realpath .)/$RESULTS_DIR/$test
        [[ -n "$SANDBOXUSER" ]] &&
            die "Neco je spatne. Je nastaven SANDBOXUSER=$SANDBOXUSER, ale $SANDBOXDIR pry neni dostupy..."
    fi
    TAGS=$(realpath .)/$RESULTS_DIR/$TAG_FILE
    TD=$TESTSDIR/$test
    mkdir -p $T || die "nepovedlo se vytvorit adresar pro test '$T'"

    # override nastaveni (napr. promenna FUT)
    if [[ -f "$TD/setup.sh" ]]; then
        . $TD/setup.sh
    fi

    if [[ -z "$SANDBOXDIR" ]]; then
        [[ -n "$FUT" ]] || die "neni nastavena promenna FUT"
        cp $FUT $T || die "nepodarilo se zkopirovat '$FUT' do '$T'"
    fi
    set +x
}

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
        cp -a $T/* $test/ 2>/dev/null || {   
            echo "$failure:$test: skript smazal test" >$test/$HODNOCENI;
            add_test_tag "scoring_${test}" ${failure};
            add_test_tag "${test}_fail" "skript smazal test";
        }
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
        add_test_tag "scoring_${test}" ${success} ${msg}
        add_test_tag "${test}_ok"
    else
        if [[ "$diff" = y ]]; then
            echo "$failure:chyba:$msg"
            echo "$d"
            add_test_tag "scoring_${test}" ${failure} ${msg};
            add_test_tag "${test}_fail";
        else
            echo "$failure:chyba:$msg viz $test/stdouterr.diff"
            add_test_tag "scoring_${test}" ${failure} "${msg} viz ${test}/stdouterr.diff";
            add_test_tag "${test}_fail";
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
# score_to_points()
# {
#     awk -v MAXSCORE=$MAXSCORE -v MAXPOINTS=$MAXPOINTS '{
#         score=$1
#         if (score < 0)
#             score = 0
#         if (score > MAXSCORE)
#             score = MAXSCORE
#         body = score*1.0 / MAXSCORE * MAXPOINTS
#         if (body > 0 && body < 1)
#             body = 1
#         print int(body+0.5)
#     }'
# }

# ve vsech souborech rekurzivne nahradi kazdy vyskyt retezce z promenne
# $IOS_.._. (jmeno promenne zjisti z $PROJECT) a retezce "$IOS.._./odevzdane" a
# nahradi ho: "/.sanitized./"
tst_sanitize()
{
    if ! in_student_dir; then
        echo "nejsme v adresari studenta! nic nenahrazuji" >&2
        return 1
    fi
    san_dir1="/asdf/"
    san_dir2="/asdf/"
    san_dir3="/asdf/"
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
#    [[ -z "$san_dir3" ]] && san_dir3=^/asdf/
    eretests="(`echo "$tests"|tr '\n' '|'|sed 's/|$//'`)"
    find . -type f -exec sed -i -r "
s#$san_dir1#/.sanitized.#g
s#$san_dir2#/.sanitized.#g
s#$san_dir3#/.sanitized.#g
s#/.sanitized./$eretests/$login#/.sanitized.#g
s#/.sanitized./$eretests#/.sanitized.#g" {} \;
}
# s#$san_dir2/odevzdane#/.sanitized.#g


# # chovani pri spusteni s parametem: sum
# tst_sum()
# {
#     # srandicky s barvickama
#     if [[ -t 1 ]]; then
#         c_red=`tput setaf 1`
#         c_normal=`tput sgr0`
#     fi 
#     # uzivatelem definovane hodnoceni uplne nahoru
#     if [[ -f $UHODNOCENI ]]; then
#         echo "#-- rucni uprava hodnoceni ----------------------------"
#         cat $UHODNOCENI
#     fi >$HODNOCENI
#     # pod to hodnoceni z testovani
#     echo "#-- automaticke hodnoceni -----------------------------" >>$HODNOCENI
#     hodnoceni=
#     for tname in $tests; do
#         if [[ -f "$tname/$HODNOCENI" ]]; then
#             if [[ `wc -l <$tname/$HODNOCENI` -gt $HODNFIRSTNLINES ]]; then
#                 cat $tname/$HODNOCENI | head -n $HODNFIRSTNLINES
#                 echo "# Vypis byl zkracen, cely text viz $tname/$HODNOCENI"
#             else
#                 cat $tname/$HODNOCENI
#             fi
#             bodytest=`grep -v ^# $tname/$HODNOCENI |
#                 awk -F: '{sum+=$1}END{print sum}'`
#                 #awk -F: '{sum+=$1}END{print int(sum+.5)}'`
#             if [[ "$bodytest" -le 0 ]]; then
#                 hodnoceni="$hodnoceni
# $c_red$tname=$bodytest$c_normal"
#             else
#                 hodnoceni="$hodnoceni
# $tname=$bodytest"
#             fi
#         fi
#     done >>$HODNOCENI
#     echo "#------------------------------------------------------" >>$HODNOCENI
# #    sum=`grep -v ^# $HODNOCENI | awk -F: '{sum+=$1}
# #        END{if (int(sum)!=sum) print int(sum+.5); else print sum}'`
# #    sum=`grep -v ^# $HODNOCENI|awk -F: '{sum+=$1}END{print int(sum+.5)}'`
#     score=`grep -v ^# $HODNOCENI|awk -F: '{sum+=$1}END{print sum}'`
#     if [[ -z "$MAXSCORE" ]]; then
#         echo "$score:celkem bodu za projekt" >>$HODNOCENI
#         sed -i "1i$score:celkem bodu za projekt" $HODNOCENI
#     else
#         echo "$score:celkove score (max pro hodnoceni $MAXSCORE)" >>$HODNOCENI
#         bodu=`score_to_points <<<$score`
# #        [[ $sum -gt $MAXPOINTS ]] && sum=$MAXPOINTS
#         echo "$bodu:celkem bodu za projekt" >>$HODNOCENI
#         sed -i "1i$bodu:celkem bodu za projekt" $HODNOCENI
#     fi
#     echo "$hodnoceni" | sed -n '2,$p'
# }


# test, pokud jsme v adresari s nazvem nejakeho studentskeho loginu
in_student_dir()
{
    [[ "$login"=="$(basename `pwd`)" ]]
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

###############################################################################
#  M A I N
###############################################################################

# bezproblemova lokalizace
export LC_ALL=C
export LANG=C

# prizpusob se prepinacum
# -d is used for recursive run of $0
[[ -n "$DEBUG" ]] && DEBUG=-d
while getopts 't:l:d' c; do
    case $c in
        d) export DEBUG=-d;; # -d is used for recursive run of $0
        t) export SANDBOXDIR=$OPTARG;;
        l) export SANDBOXLOCK=$OPTARG;;
    esac
done
shift $((OPTIND-1))

# automaticka detekce adresare testu
if [[ -z "$TESTSDIR" ]]; then
    TESTSDIR=$(dirname $(dirname $(realpath $0)))
fi

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

# fronta a zamek pro vzajemne vylouceni testu
if [[ -n "$SANDBOXLOCK" ]]; then
    LOCKDIR=$SANDBOXLOCK
else
    LOCKDIR=$TESTSDIR/locks
fi

# nacti hodnoceni
[[ -n "$PEDANTIC" ]] && SCORING_FILE=$SCORING_PEDANTIC
[[ -n "$SCORING" ]] && SCORING_FILE=$SCORING
if [[ -f $TESTSDIR/$SCORING_FILE ]]; then
    . $TESTSDIR/$SCORING_FILE
else
    die "Nemohu najit soubor s ohodnocenim $TESTSDIR/$SCORING_FILE"
fi


[[ -n "$TEST_FILE" ]] || TEST_FILE=dotest.sh
[[ -n "$RESULTS_DIR" ]] || RESULTS_DIR=tests

if [[ -z "$login" ]]; then
    die "Neni nastavena promenna login"
fi

if [[ -z "$TAG_FILE" ]]; then
    die "Neni nastavena promenna TAG_FILE"
fi

if [[ -z "$FUT" ]]; then
    die "Neni nastavena promenna FUT"
fi

# ziskani jmen vsech testu
tests=`ls $TESTSDIR | 
    while read f; do [ -f "$TESTSDIR/$f/$TEST_FILE" ] && echo "$f"; done`



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
    # sum) tst_sum;;
    clean) tst_clean;;
    student) in_student_dir;;
    *) help;;
esac
