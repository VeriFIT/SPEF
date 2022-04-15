

# run testsuite in container (/opt/tests, /opt/results, /opt/sut)

export PATH=/opt/tests/src:$PATH
export TESTSDIR=/opt/tests
export TEST_FILE=dotest.sh
export login=sut
/opt/tests/testsuite.sh
