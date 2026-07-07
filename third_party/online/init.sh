#!/bin/bash
work_dir=`dirname $0`
work_dir=`cd $work_dir;pwd`
cd $work_dir

source bashrc.sh
bash -x init_real.sh &
pid=$!

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