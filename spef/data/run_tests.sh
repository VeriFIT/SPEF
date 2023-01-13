# run_tests tst_file tests_dir TESTS_TAGS RESULTS_DIR login fut
tst_script=$1
export TESTSDIR=$2
export TAG_FILE=$3
export RESULTS_DIR=$4
export login=$5
export FUT=$6
export TEST_FILE=dotest.sh
shift 6
for test_name in "$@"
do
    $tst_script run $test_name
done