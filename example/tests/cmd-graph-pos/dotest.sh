[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog graph-pos test.log
auto_report "prikaz graph-pos"
