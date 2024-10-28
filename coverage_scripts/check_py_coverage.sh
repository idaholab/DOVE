#!/bin/bash
SCRIPT_DIRNAME=`dirname $0`
DOVE_DIR=`(cd $SCRIPT_DIRNAME/..; pwd)`
cd $DOVE_DIR
RAVEN_DIR=`python -c 'from src._utils import get_raven_loc; print(get_raven_loc())'`

source $DOVE_DIR/coverage_scripts/initialize_coverage.sh

#coverage help run
SRC_DIR=`(cd src && pwd)`
# For some reason, when the --source and --omit flags for coverage run in line 19 contain files with bash-style ("/c/*")
# file paths, coverage.py does not interpret them correctly. It would seem to treat them as relative file paths.
# This only occurs in DOVE, only when running through rook. These lines edit the src path to instead start with "C:".
# TODO figure out why this happens and fix it there if possible
echo $SRC_DIR
if [[ "$SRC_DIR" == "/c"* ]]
then
    echo $SRC_DIR
    SRC_DIR="C:${SRC_DIR:2}"
else
    echo "It still didn't work"
fi

export COVERAGE_RCFILE="$SRC_DIR/../coverage_scripts/.coveragerc"
echo $SRC_DIR
SOURCE_DIRS=($SRC_DIR)
echo $SOURCE_DIRS
OMIT_FILES=($SRC_DIR/Dispatch/twin_pyomo_test.py,$SRC_DIR/Dispatch/twin_pyomo_test_rte.py,$SRC_DIR/Dispatch/twin_pyomo_limited_ramp.py,$SRC_DIR/Dispatch/twin_pyomo_test_ch_disch.py)
EXTRA="--source=${SOURCE_DIRS[@]} --omit=${OMIT_FILES[@]} --parallel-mode"
export COVERAGE_FILE=`pwd`/.coverage

coverage erase
($RAVEN_DIR/run_tests "$@" --re=DOVE/tests --python-command="coverage run $EXTRA" ||
                                            echo run_tests done but some tests failed)

## Prepare data and generate the html documents
coverage combine
coverage html

# See report_py_coverage.sh file for explanation of script separation
(bash $DOVE_DIR/coverage_scripts/report_py_coverage.sh --data-file=$COVERAGE_FILE --coverage-rc-file=$COVERAGE_RCFILE)
