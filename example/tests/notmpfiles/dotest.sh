[ -x $T/tradelog ] || return
cd $T
cp $TD/test.log .
run_test strace -f \
    -o trace -e trace=open,creat ./tradelog list-tick test.log &>/dev/null
egrep -v '(\+\+\+|---|NOENT)' trace |
    egrep '(creat\(|open\(.*O_RDWR|open\(.*O_WRONLY)' | 
    egrep -v '(/dev|cmds.log|wedirc|/tmp/sh-thd-|/proc/self/task)' |
    sed 's/.*"\(.*\)".*/\1/' | sort -u >temp_files
[ -z "$DEBUG" ] && rm trace
if [ `wc -l <temp_files` -lt 1 ]; then
    echo $success:ok: docasne soubory: `cat temp_files`
    arg=`cat temp_files`
    add_test_tag "scoring_${test}" ${success} "docasne soubory" "$arg"
    add_test_tag "${test}_ok"
else
    echo $failure:$test: docasne soubory: `cat temp_files`
    arg=`cat temp_files`
    add_test_tag "scoring_${test}" ${failure} "docasne soubory" "$arg"
    add_test_tag "${test}_fail"
fi
