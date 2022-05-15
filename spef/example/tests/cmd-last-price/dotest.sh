[ -x $T/tradelog ] || return
cp $TD/test.log $T
cd $T
run_test ./tradelog last-price test.log
auto_report "prikaz last-price"
