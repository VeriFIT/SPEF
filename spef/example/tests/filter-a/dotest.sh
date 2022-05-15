[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog -a "2021-01-11 17:59:58" test.log
auto_report "filtr -a"
