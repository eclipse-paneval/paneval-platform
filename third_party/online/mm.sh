#!/bin/bash
work_dir=`dirname $0`
work_dir=`cd $work_dir;pwd`
cd $work_dir

source bashrc.sh

export PATH=/root/miniconda3/bin:$PATH

batch_id=$1
log_path=$2
export OUTPUT_PREFIX=$3
port=$4

env_root=/share/project/mmenv
if [ ! -d "$env_root" ]; then
    # 若不存在，则创建目录
    mkdir -p "$env_root"
    echo "mk: $env_root"
else
    echo "root exists"
fi

fenv_dir=$env_root/$batch_id

cat > $fenv_dir/__paneval__/config.json
a=$(python ./evals.py $fenv_dir/__paneval__/config.json)
eval "$a"

python ./mm.py $fenv_dir/__paneval__/config.json $fenv_dir/meta.json $fenv_dir/__paneval__ $fenv_dir
export PYTHONPATH="$fenv_dir/__paneval__/flag-eval-mm:$PYTHONPATH"

(bash -ex $fenv_dir/__paneval__/bootstrap.sh $log_path $port 2>&1 | tee -a $log_path.out) &
pid=$!
fenv_dir1=$work_dir/env
echo $pid > $fenv_dir1/$batch_id.pgid

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
rm $fenv_dir1/$batch_id.pgid
