[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog -t TSM -t NVDA test.log
auto_report "filtr -t -t"
