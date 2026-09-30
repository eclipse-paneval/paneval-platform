#!/bin/bash
set -e

work_dir=$(cd -- "$(dirname -- "$0")" && pwd)

if [ ! -d "$work_dir/paneval" ]; then
    code_archive=$(find "$CONDA_DATASET_DOWNLOAD_PATH" -name 'paneval.tar.gz')
    mkdir "$work_dir/paneval"
    tar -zxf "$code_archive" -C "$work_dir/paneval"
fi

# run_online rsyncs internal/ alongside this script for every attempt.
# Copy after extraction, including when reusing an existing evaluator tree.
mkdir -p "$work_dir/paneval/internal"
cp -a "$work_dir/internal/." "$work_dir/paneval/internal/"
