
# export PATH=/opt/tests/src:$PATH
# export TESTSDIR=/opt/tests
# export TAG_FILE=tests_tags.yaml
# export login=sut
# export TEST_FILE=dotest.sh
# export RESULTS_DIR=tests
# /opt/tests/testsuite.sh

# $1 = tst fce
# $2 = tests dir
# $3 = test file
# $4 = tests results dir
# $5 = sut
# $6 = fut
# run_testsuite /opt/tests/src /opt/tests tests_tags.yaml tests sut {fut}
export PATH=$1:$PATH
export TESTSDIR=$2
export TAG_FILE=$3
export RESULTS_DIR=$4
export login=$5
export FUT=$6
export TEST_FILE=dotest.sh
$TESTSDIR/testsuite.sh
