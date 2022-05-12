[ -x $T/tradelog ] || return
cp $TD/test*.log $T
cd $T
run_test ./tradelog test1.log test2.log test3.log
auto_report "opis vice vstupnich souboru na vystup"
