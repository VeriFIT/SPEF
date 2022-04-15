[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog pos test.log
auto_report "prikaz pos"
