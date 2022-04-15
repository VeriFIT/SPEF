#!/usr/bin/env bash
# ***** write test strategy here *****


# je tst v ceste?
type tst &>/dev/null || { echo "chyba: prikaz tst neni v ceste"; exit 1; }
type n &>/dev/null || { echo "chyba: prikaz n neni v ceste"; exit 1; }


# jsme v adresari nejakeho studenta?
[ "$nostud" ] || tst student || 
    { echo "test proved v adresari studenta"; exit 1; }

chmod +rx tradelog &>/dev/null
if file tradelog | grep -q CRLF; then
    dos2unix tradelog
    n crlf
fi



# a provedeme jednotlive testy
tst clean

ulimit -f 2048

if [ -n "$NOPAR" ]; then
    echo "testuju sekvencne"
    while read t; do tst run $t; done
else
    tst run_concurrently
fi <<EOF
notmpfiles
cat1
cat2
cat3
cat4
cmd-list-tick
cmd-last-price
cmd-profit
cmd-pos
cmd-hist-ord
cmd-graph-pos
filter-a
filter-b
filter-ab
filter-tick-cat
filter-tick-cat2
filter-tick-pos
filter-tick-profit
EOF

echo "testsuite done"

tst sanitize
tst sum >/dev/null

# at vysledky mohou cist vsichni ve skupine (napr. netestovaci uzivatel)
chmod -R g+rX . 2>/dev/null
