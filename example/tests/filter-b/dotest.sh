[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog -b "2021-01-12 15:43:10" test.log
auto_report "filtr -b"
