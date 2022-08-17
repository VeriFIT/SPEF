[ -x $T/tradelog ] || return
cd $T
run_test ./tradelog
auto_report "opis stdin na stdout"
