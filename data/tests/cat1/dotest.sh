[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog test.log
auto_report "opis vstupniho souboru na vystup"
