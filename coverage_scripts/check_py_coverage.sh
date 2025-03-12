#!/bin/bash
SCRIPT_DIRNAME=`dirname $(readlink -f "$0")`
DOVE_LOC=`(cd $SCRIPT_DIRNAME/..; pwd)`
cd $DOVE_LOC

# Add parent dir of DOVE to path to allow imports from DOVE
DOVE_DIR=`(cd $DOVE_LOC/..; pwd)`
OLD_PYTHONPATH=$PYTHONPATH
    if [[ "$OLD_PYTHONPATH" == "" ]]; then
      export PYTHONPATH="$DOVE_DIR"
    else
       export PYTHONPATH="$OLD_PYTHONPATH:$DOVE_DIR"
    fi

RAVEN_DIR=`python -c 'from src._utils import get_raven_loc; print(get_raven_loc())'`
if [[ "$RAVEN_DIR" != *"raven" ]]
then
  # If raven directory has been added to PYTHONPATH or is pip installed, get_raven_loc will return ravenframework
  if [[ "$RAVEN_DIR" == *"ravenframework" ]]  # get_raven_loc might return ravenframework, not raven
  then
    RAVEN_DIR=`(cd $RAVEN_DIR/..; pwd)`  # Take parent directory, which should be raven directory, instead
    if [[ "$RAVEN_DIR" != *"raven" ]]  # With a pip installed raven, this would be "site-packages"
    then
      echo "Must have git cloned (not pip installed) raven to run tests. Expected 'raven' directory at $RAVEN_DIR."
      exit
    fi
  else
    echo "Expected 'raven' or 'ravenframework' directory; found '$RAVEN_DIR' instead."
    exit
  fi

fi

export REGEX=`cd tests; pwd` # Default regex value for run_tests
if [[ "$REGEX" == "/c/"* ]] # The path should be in Windows format if it's a Windows path
then
  REGEX="C:${REGEX:2}"
  REGEX="${REGEX//\//\\}"
fi

source $DOVE_LOC/coverage_scripts/initialize_coverage.sh

#coverage help run
SRC_DIR=`(cd src; pwd)`
# coverage.py does not like windows paths that start with /c/ instead of C:/
if [[ "$SRC_DIR" == "/c/"* ]]
then
    SRC_DIR="C:${SRC_DIR:2}"
fi

export COVERAGE_RCFILE="$SRC_DIR/../coverage_scripts/.coveragerc"
SOURCE_DIRS=($SRC_DIR)
OMIT_FILES=($SRC_DIR/Dispatch/twin_pyomo_test.py,$SRC_DIR/Dispatch/twin_pyomo_test_rte.py,$SRC_DIR/Dispatch/twin_pyomo_limited_ramp.py,$SRC_DIR/Dispatch/twin_pyomo_test_ch_disch.py)
EXTRA="--source=${SOURCE_DIRS[@]} --omit=${OMIT_FILES[@]} --parallel-mode"
export COVERAGE_FILE=`pwd`/.coverage
coverage erase
($RAVEN_DIR/run_tests "$@" --re=$REGEX --python-command="coverage run $EXTRA" ||
                                            echo run_tests done but some tests failed)

# Prepare data and generate the html documents
coverage combine
coverage html

# See report_py_coverage.sh file for explanation of script separation
(bash $DOVE_LOC/coverage_scripts/report_py_coverage.sh --data-file=$COVERAGE_FILE --coverage-rc-file=$COVERAGE_RCFILE)
