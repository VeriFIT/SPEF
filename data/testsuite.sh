#!/usr/bin/env bash
# ***** write test strategy here *****
chmod +rx tradelog &>/dev/null

ulimit -f 2048

while read t; do tst run $t; done<<EOF
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

# at vysledky mohou cist vsichni ve skupine (napr. netestovaci uzivatel)
chmod -R g+rX . 2>/dev/null
