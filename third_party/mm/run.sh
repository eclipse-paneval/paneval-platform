#!/bin/bash
work_dir=`dirname $0`
work_dir=`cd $work_dir;pwd`
cd $work_dir

task_name=$1
name=$2
output=$3
log_path=$4
batch_id=$5
taskResultId=$6
idx=$7
lbx=$8
data_root=$9
data_root_path=${10}
try_run=${11}

cp_path=`/root/miniconda3/bin/python gen.py --func=get_checkpoint 2>>$log_path`
eva_name=`/root/miniconda3/bin/python gen.py --func=eva_name`
starttime=`date +'%Y-%m-%d %H:%M:%S'`
#server
if [ $lbx -eq 1 ]; then
    nohup /root/miniconda3/bin/python evalmm/server/run_server.py --config $task_name --output-dir=$output --checkpoint=$cp_path --data-root=$data_root_path &
    pid=$!
else
    nohup /root/miniconda3/bin/python evalmm/server/run_server.py --config $task_name --output-dir=$output --checkpoint=$cp_path $try_run &
    pid=$!
fi
sleep 30

#client
cd ../
echo "begin run client run.sh..." >>$log_path
bash -x run.sh $name http://127.0.0.1 5000 > $log_path 2>&1
ret=$?
cd -

if [ $ret -eq 0 ];then
    /root/miniconda3/bin/python tools/evaluate.py --model-name="$eva_name" --config=$task_name --output-dir=$output $try_run
    ret=$?
    endtime=`date +'%Y-%m-%d %H:%M:%S'`
    cd ..
    if [ $ret -eq 0 ];then
        # wenjian=$out_dir/$task_name/result.json
        cat $output/*_result.json | /root/miniconda3/bin/python gen.py --func=write --idx=$idx --output=$output --data=$batch_id --path=$taskResultId --starttime="$starttime" --endtime="$endtime" 2>>$log_path
        ret=$?
    else
        echo "" | /root/miniconda3/bin/python gen.py --func=write --data=$batch_id --output=$output --idx=$idx --path=$taskResultId --starttime="$starttime" --endtime="$endtime" 2>>$log_path
        ret=$?
    fi
else
    cd ..
    endtime=`date +'%Y-%m-%d %H:%M:%S'`
    echo "" | /root/miniconda3/bin/python gen.py --func=write --data=$batch_id --output=$output --idx=$idx --path=$taskResultId --starttime="$starttime" --endtime="$endtime" 2>>$log_path
fi
kill -9 $pid
echo $ret
