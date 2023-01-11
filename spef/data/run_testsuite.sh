# run_testsuite /opt/tests/src /opt/tests tests_tags.yaml tests sut {fut}
export PATH=$1:$PATH
export TESTSDIR=$2
export TAG_FILE=$3
export RESULTS_DIR=$4
export login=$5
export FUT=$6
export TEST_FILE=dotest.sh
$TESTSDIR/testsuite.sh