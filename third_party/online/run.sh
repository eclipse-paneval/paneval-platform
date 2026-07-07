#!/bin/bash
work_dir=`dirname $0`
work_dir=`cd $work_dir;pwd`
cd $work_dir

source bashrc.sh

batch_id=$1
src=$2
export MODEL_PATH=$3
export LOG_PATH=$4
export THIRD_PARTY=$MODEL_PATH/__paneval__
export EVAL_LOG_PATH=$5

fenv_dir=/share/project/eval_results/env

a=`cat`
eval "$a"

cd $THIRD_PARTY
bash -ex $THIRD_PARTY/bootstrap.sh $LOG_PATH >> $LOG_PATH.out 2>&1  &
pid=$!
echo $pid > $fenv_dir/$batch_id.pgid
while [ 1 ]; do
    x=`ps -p $pid | tail -n 1 | awk '{print $1}'`
    if [ $x -eq $pid ]; then
        # 不能用wait。必须echo。因为ssh如果不echo，30分钟左右后会超时，很坑。
        echo "x"
        sleep 10
    else
        break
    fi
done
rm $fenv_dir/$batch_id.pgid
#rm -rf $FEAM_VENV-*
