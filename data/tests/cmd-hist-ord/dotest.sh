[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog hist-ord test.log
auto_report "prikaz hist-ord"
