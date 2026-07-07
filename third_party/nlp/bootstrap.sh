#!/bin/bash

# These variables are defined by environment.
#
# export MODEL_PATH=$1
# export THIRD_PARTY=$1/__paneval__/
# export LOG_PATH=$2
#
# FEAM_VENV=/tmp/venv-{package}
# FEAM_PYTHON=$FEAM_VENV/bin/python
# FEAM_PIP=$FEAM_VENV/bin/pip
source $THIRD_PARTY/pre_bootstrap.sh

SUPERVISORD_CONF_PATH=/tmp/supervisord.conf
SUPERVISORCTL="supervisorctl -c $SUPERVISORD_CONF_PATH"


if [[ -e "$MODEL_PATH/requirements.txt" ]]
then
    pip install $PYPI_INDEX_OPTS -r $MODEL_PATH/requirements.txt
fi

if which nvidia-smi
then
    if nvidia-smi
    then
        echo
    fi
fi

# https://huggingface.co/docs/transformers/installation#cache-setup
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export HF_DATASETS_CACHE="${HF_HOME}/datasets"
export TRANSFORMERS_CACHE=$HUGGINGFACE_HUB_CACHE

pushd "$THIRD_PARTY" || exit 1
if [[ ! -e "$HF_HOME" ]]
then
    mkdir -p "$HF_HOME"
fi

popd || exit 1


printenv
# unset HF_DATASETS_CACHE
