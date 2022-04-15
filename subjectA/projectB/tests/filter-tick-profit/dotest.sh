[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog -t TSM profit test.log
auto_report "filtr -t profit"
