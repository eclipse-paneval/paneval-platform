#!/bin/bash
set -x
printenv

if [[ "$PIP_CACHE_DIR" != "" ]]
then
    if [[ ! -e "$PIP_CACHE_DIR" ]]
    then
        mkdir -p $PIP_CACHE_DIR
    fi
    PYPI_INDEX_OPTS="$PYPI_INDEX_OPTS --cache-dir $PIP_CACHE_DIR"
fi
export PYPI_INDEX_OPTS
python -V
pip --version
