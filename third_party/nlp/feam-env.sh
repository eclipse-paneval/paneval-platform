#!/bin/bash
set -ex

# Override feam venv by the first position argument
FEAM_VENV=$1
PACKAGE=$2
export FEAM_BIN=$FEAM_VENV/bin
export FEAM_PIP=$FEAM_BIN/pip
export FEAM_PYTHON=$FEAM_BIN/python

FULL_CONDA_ENV="conda-full-${PACKAGE}.tar.gz"
export FULL_CONDA_ENV

if [ -n "$(find "$CONDA_DATASET_DOWNLOAD_PATH" -name "$FULL_CONDA_ENV")" ]; then
    FULL_CONDA_ENV_TAR=$(find "$CONDA_DATASET_DOWNLOAD_PATH" -name "$FULL_CONDA_ENV")
    export FULL_CONDA_ENV_TAR
    mkdir -p "$FEAM_VENV" && tar -zxf "$FULL_CONDA_ENV_TAR" -C "$FEAM_VENV"
    source "${FEAM_VENV}/bin/activate"
fi

pushd "$THIRD_PARTY" || exit 1

install_deps() {
    set -e
    WORKDIR=feam-${PACKAGE}
    mkdir -p $WORKDIR
    tar -zxf ${WORKDIR}.tar.gz -C ./${WORKDIR}

    pushd ${WORKDIR}
    $FEAM_PIP install $PYPI_INDEX_OPTS --upgrade poetry 'pip<24.1' certifi && \
        $FEAM_BIN/poetry build && \
        $FEAM_PIP install $PYPI_INDEX_OPTS dist/*.whl
    popd

    $FEAM_PIP install $PYPI_INDEX_OPTS -U 'datasets<3' tiktoken transformers_stream_generator

    $FEAM_PIP install $PYPI_INDEX_OPTS --upgrade transformers==4.40.2  #  For HuggingFace tokenizer #Qwen2Tokenizer, qwen2_moe
    $FEAM_PIP install $PYPI_INDEX_OPTS filelock
}


if [[ "$FULL_CONDA_ENV_TAR" == "" ]]
then
    install_deps
fi
TOKENIZER_REQUIREMENTS="$THIRD_PARTY/tokenizer/requirements.txt"
if [[ -f "$TOKENIZER_REQUIREMENTS" ]];then
    $FEAM_PIP install $PYPI_INDEX_OPTS --upgrade -r "$TOKENIZER_REQUIREMENTS"
fi
$FEAM_PIP install $PYPI_INDEX_OPTS 'httpx[socks]'
popd || exit 1
