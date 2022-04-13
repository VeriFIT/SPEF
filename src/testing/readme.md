
# NOVY PROJEKT
1. vytvor novy adresar pre projekt: napr. proj1
2. vojdi do adresara proj1
3. pomocou menu (F2) vyber moznost vytvorit novy projekt
    -s tym sa ti vytvori konfiguracny subor "proj_conf.yaml" v adresari proj1
4. uprav hodnoty v proj1/proj_conf.yaml pre dany projekt
5. vytvor testy
    1. pomocou menu (F2) vyber moznost vytvorit novy test
        -s tym sa ti vytvori adresar pre testy "tests", ktory obsahuje:
            "test1/"                -adresar pre novy test
            "test1/dotest.sh"       -subor pre samotny test
            "test1/test_tags.yaml"  -subor s tagmi testu
            "scoring"               -subor pre hodnotenie testov (premenne test1_ok a test1_fail)
            "sum"                   -subor pre vypocet celkoveho hodnotenia
            "testsuite.sh"          -subor pre testovaciu strategiu
            "testsuite_tags.sh"     -subor s tagmi testovacej sady
            "src/fce"               -subor s funkciami pre dotest.sh
            "src/tst"               -subor s funkciami pre testsuite.sh
            "history/"              -adresar pre uchovavanie historie testov
7. implementuj testy (subor dotest.sh)
    -mozes vyuzivat funkcie definovane v "tests/src/fce"
    -dotest.sh vykona spustenie testu
8. implementuj testovaciu strategiu (subor testsuite.sh)
    -mozes vyuzivat funkcie definovane v "tests/src/tst"
9. uprav subor scoring


tests_dir = os.path.join(proj_dir, TESTSDIR)
test_file = dotest.sh

prepare.sh
"""
export PROJDIR={proj_dir}
export TESTSDIR={tests_dir}
export TEST_FILE={test_file}
export TD={tests_dir}/{test_name}
export T={solution_dir}/{tests}/{testname}

export FUT={env.cwd.proj.sut_required}
export SCORING_FILE={scoring}
export SCORING_PEDANTIC=

export test
export login

PROJDIR=
TESTNAME=


export TESTSDIR=$PROJDIR/tests
export TEST_FILE=dotest.sh
export TD=$TESTSDIR/$TESTNAME
export T=
export FUT=
export SCORING_FILE={scoring}
export SCORING_PEDANTIC=

SCORING_FILE=scoring
SCORING_PEDANTIC=scoring-pedantic

HODNOCENI=hodnoceni-auto
UHODNOCENI=hodnoceni-user

SPUSTENI=spusteni

"""



# PRED SPUSTENIM TEST/TESTSUITE
- podporovane premenne:
    * PROJDIR       adresar projektu
    * TESTSDIR      adresar s testami
    * TD            zdrojovy adresar testu (test dir)
    * T             novo vytvoreny adresar urceny pre vysledky testu (login/tests/test/)
    * FUT           subor ktory sa testuje (file under test)
    * test
    * login

- podporovane funkcie:
    * export PATH="tests/src":$PATH     export funkcii v src/
    * . "tests/src/fce"                 import funkcii zo src/fce



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


#  1. CO A JAK PRIPRAVIT U NOVEHO PROJEKTU


# 1. Priprav si, co a jak hodnotit a jak to roztridit do jednotlivych testu
# 2. Vytvor soubor s hodnocenim (scoring). Tento soubor obsahuje definici
#    promenne:
#    -  PROJECT  (obsahuje jmeno promenne, ve ktere je jmeno adresare s korenem
#           vsech testovacich zalezitosti -- pro tst sanitize, nepovinne)
#    -  PROJDIR  (adresar s korenem projektu obsahujici testovaci skripty a
#           odevzdana reseni)
#    -  MAXPOINT (maximalni pocet bodu za projekt),
#    -  MAXSCORE (maximalni score, pokud da soucet testu vic nez MAXPOINT -- na
#           body to bude prepocteno pomerem MAXPOINT/MAXSCORE, nepovinne) a
#    -  definici promennych s jejich float hodnotami. Tyto promenne bys mel
#       pouzivat ve skriptu `dotest.sh' pri vypisovani, jak moc hodnotis
#       vysledek daneho testu (viz nize). Pri spusteni `dotest.sh' (viz nize)
#       budou tyto promenne nastaveny v prostredi, takze je dotest.sh muze
#       vyuzit.

# 4. Vytvor strategii testovani v souboru `testsuite', tj.:
#    a) kontrola, jestli tam studentsky skript je
#    b) prevedeni na unixove ukonceni radku, +x mod, ...
#    c) spusteni jednotlivych testu tak, jak to chces poporade, pomoci:
#       tst run jmeno_testu [args...]
#    d) nebo spusteni vybranych testu paralelne pomoci:
#       tst run_concurrently <<EOF
#       test1 [args...]
#       test2 [args...]
#       ...
#       testn
#       EOF
# 5. V path/to/testing/bin/ vytvor:
#     a) tst: /path/to/tst "$@" | grep -v Terminated
#     b) t: /path/to/testsuite "$@"
#     c) n: skript, ktery ti bude vkladat do souboru $UHODNOCENI caste poznamky
#     d) s: tst sum
#    Pak:
#     $ cd xlogin00
#     $ t
#     ...provadim testy
#     $ ...rucni inspekce kodu a vysledku
#     $ n pricti_odecti_X_bodu_se_zduvodnenim_Y
#     $ s


# Rekapitulace promennych konfigurujici chovani testu:
#    PEDANTIC - neprazdny retezec zpusobi pouziti $SCORING_PEDANTIC hodnoceni
#    SCORING  - urcuje soubor s hodnocenim (ma prioritu pred PEDANTIC)
#    TIMEOUT  - timeout (se suffixem jednotky) pro jeden test
# Promenne nastavene pro `dotest.sh':
#    TESTSDIR - adresar s testy
#    TD       - adresar s definici aktualne provadeneho testu
#    T        - vytvoreny adresar urceny pro vysledky testu
# Rekapitulace adresarove struktury testu:
#    tests/
#    |- lock/            - adresar pro zamky testu
#    |- test_name1/      - adresar s jednim testem
#    |  |- setup.sh      - skript pro pripravu testu (napr. nastaveni
#                          test-specific hodnoty promenne FUT nebo TIMEOUT)
#    |  |- dotest.sh     - skript pro provedeni testu
#    |  |- errcode.ref   - (doporucene) referencni navratovy kod pro `diffall'
#    |  |- stdin.ref     - (doporucene) presmerovany vstup pro testovany skript
#    |  |- stdout.ref    - (doporucene) referencni vystup pro `diffni/diffall'
#    |  `- stderr.ref    - (doporucene) referencni chyb. vystup pro `diffall'
#    |- scoring          - soubor s hodnoticimi parametry a MAXPOINT
#    |- scoring_pedantic - (nepovinne) pedanticka varianta hodnoceni
#    |- testsuite        - (doporucene) strategie, vola 
#    |                          "tst run test_name1",
#    |                          "tst run test_name args ..." 
#    |                              (args ... budou predany skriptu test_name/dotest.sh)
#    |                          "tst sum"
#    |- wrappers/        - adresar s wrappery (pro testovani skriptu, viz
#    |                     funkce wrappers_on a wrappers_off pouzivane v
#    |                     dotest.sh)
#    `- tst              - tento skript

