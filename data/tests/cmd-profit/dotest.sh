[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog profit test.log
auto_report "prikaz profit"
