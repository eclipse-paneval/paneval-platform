#!/bin/bash
work_dir=`dirname $0`
work_dir=`cd $work_dir;pwd`
cd $work_dir

fenv_dir=/share/project/eval_results/env

source bashrc.sh

batch_id=$1

if [ -f $fenv_dir/$batch_id.pgid ]; then
    pstree -p `cat $fenv_dir/$batch_id.pgid` | grep -oP '\(\d+\)' | grep -oP '\d+' | while read line; do
        pgroup_id=$(ps -o pgid= -p $line)
        kill -9 $line $pgroup_id
    done
    rm $fenv_dir/$batch_id.pgid
    rm -rf $fenv_dir/venv.$batch_id*
fi
