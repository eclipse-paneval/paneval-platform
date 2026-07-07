#!/bin/bash

PACKAGE=$1
VENV="${FEAM_VENV}-${PACKAGE}"
FEAM_PYTHON=$VENV/bin/python
# Create Python virtual enviroment.
bash -x $THIRD_PARTY/feam-env.sh $VENV $PACKAGE

$FEAM_PYTHON run_prepare.py $PACKAGE
