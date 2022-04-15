[ -x $T/tradelog ] || return
cp $TD/test*.log* $T
cd $T
run_test ./tradelog test1.log test2.log.gz test3.log.gz
auto_report "opis vice vstupnich souboru vcetne gz na vystup"
