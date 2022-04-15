[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog list-tick test.log
auto_report "prikaz list-tick"
