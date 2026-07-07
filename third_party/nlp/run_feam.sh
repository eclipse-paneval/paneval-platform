#!/bin/bash

# A wrapper to run run_feam.py:

PACKAGE=$1
export RUNNING_PACKAGE=$PACKAGE
NUM_THREADS=$2
export VENV="${FEAM_VENV}-${PACKAGE}"
FEAM_PYTHON=$VENV/bin/python

pushd $THIRD_PARTY

WORKERS=1

for contexts in ${PACKAGE}*-contexts.json
do
    if [[ "$NUM_THREADS" == "" ]]
    then
        $FEAM_PYTHON run_feam.py -p $PACKAGE -c $contexts -d $DRY_RUN_BATCH -w $WORKERS >> $EVAL_LOG_PATH 2>&1
    else
        $FEAM_PYTHON run_feam.py -p $PACKAGE -c $contexts -d $DRY_RUN_BATCH -n $NUM_THREADS -w $WORKERS >> $EVAL_LOG_PATH 2>&1
    fi
done
popd
