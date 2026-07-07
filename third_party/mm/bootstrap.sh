#!/bin/bash
work_dir=`dirname $0`
work_dir=`cd $work_dir;pwd`
cd $work_dir

log_path=$1
port=$2

if [ "x$port" == "x" ];then
    port=5000
fi

if [ -d "$work_dir/paneval" ]; then
    echo "this is online"
else
    CODE_TAR_GZ=$(find $CONDA_DATASET_DOWNLOAD_PATH -name 'paneval.tar.gz')
    mkdir ./paneval
    tar -zxf $CODE_TAR_GZ -C ./paneval
fi
if [ -d "/root/miniconda3" ]; then
    echo "Directory exists"
else
    CONDA_TAR_GZ=$(find $CONDA_DATASET_DOWNLOAD_PATH -name 'conda-full-evalmm.tar.gz')
    mkdir /root/miniconda3
    tar -zxf $CONDA_TAR_GZ -C /root/miniconda3
    apt-get update | cat
    apt-get install -y psmisc | cat
    apt-get install -y lsof | cat
    apt-get install -y curl | cat
    apt install -y libgl1-mesa-glx | cat
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        if [[ $ID == "ubuntu" ]]; then
            apt-get update | cat
            apt-get install -y tzdata | cat
            TZ=Asia/Shanghai
        elif [[ $ID == "centos" ]]; then
            yum update -y | cat
            yum install -y tzdata | cat
            TZ=Asia/Shanghai
            ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime | cat
        elif [[ $ID == "debian" ]]; then
            apt update | cat
            apt install -y tzdata | cat
            TZ=Asia/Shanghai
            apt install -y dnsutils | cat
        else
            echo "install tzdata and dnsutils error"
        fi
    else
        echo "unknown: install tzdata and dnsutils error"
    fi
fi
pythonm=/root/miniconda3/bin/python


export PYTHONPATH="./:$work_dir/paneval:$PYTHONPATH"
# export EVALMM_API_KEY="TODO"
# export EVALMM_BASE_URL="TODO"
export HF_ENDPOINT='https://hf-mirror.com'
export HF_HOME='/share/project/huggingface-240306'

if [ -d "~/.cache/torch/hub/checkpoints" ]; then
    echo "Directory exists"
fi
if [ -d "/root/.cache/evalmm/datasets" ]; then
    echo "new Directory exists"
else
    mkdir -p ~/.cache/evalmm
    ln -s $DATASETS_DATASET_DOWNLOAD_PATH  ~/.cache/evalmm/datasets
fi

tryrun=`$pythonm helper.py tryrun 2>>$log_path`
tasks=`$pythonm helper.py tasks 2>>$log_path`
adapter=`$pythonm helper.py adapter 2>>$log_path`
HF_PRETRAINED=`$pythonm helper.py nlp-pretrained 2>>$log_path | cat`
online=`$pythonm helper.py online 2>>$log_path`
out_dir=$work_dir/outputs
mkdir $out_dir

is_model_pretrained_ready() {
    model_pretrained_path=$1
    if [[ ! -e "$model_pretrained_path" ]]
    then
        return 1
    fi
    n_incomplete=$(find $model_pretrained_path -name '*.aria2' | wc -l)
    if [[ "$n_incomplete" -gt 0 ]]
    then
        return 1
    fi
    return 0
}

if [[ "$HF_PRETRAINED" != "" ]]; then
    if [ "x$online" == "x0" ]; then
        if [[ "${HF_PRETRAINED:0:1}" != "/" ]]
        then
            echo "Start to download model from HuggingFace..."
            echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
            apt-get install -y -q aria2 git-lfs > /dev/null 2>&1
            MODEL_PRETRAINED_NAME=$(echo "${EVALUATION_MODEL_NAME}" | awk -F '/' '{print $2}')
            export MODEL_PRETRAINED_NAME
            export MODEL_PRETRAINED_PATH="/share/project/huggingface/models/${MODEL_PRETRAINED_NAME}"
            if ! is_model_pretrained_ready "$MODEL_PRETRAINED_PATH"
            then
                dir=$(dirname "$MODEL_PRETRAINED_PATH")
                if [[ ! -e "$dir" ]]
                then
                    mkdir -p "$dir"
                fi

                downloadsucc=1
                HF_USERNAME=$(huggingface-cli whoami | head -1)
                HF_TOKEN=$(cat "${HF_HOME}/token")
                while [ $downloadsucc -eq 1 ]; do
                bash hfd.sh $HF_PRETRAINED $MODEL_PRETRAINED_PATH --tool aria2c -x 4 --hf_username "$HF_USERNAME" --hf_token "$HF_TOKEN"

                if find "$MODEL_PRETRAINED_PATH" -maxdepth 1 -type f -size 0 | read; then
                    echo "存在大小为0的文件"
                    echo 'Retrying...'
                    sleep 10
                    continue
                fi

                if find "$MODEL_PRETRAINED_PATH" -maxdepth 1 -type f -name "*.aria2" | read; then
                    echo "存在后缀为aria2的文件"
                    echo 'Retrying...'
                    sleep 10
                    continue
                fi
                downloadsucc=0
                done

            fi
            export REMOTE_API="hf://$MODEL_PRETRAINED_PATH"
            echo "Download model from HuggingFace is done!"
            NUM_THREADS=1  # Loading model locally doesn't need to run parellel
            CUDA_VISIBLE_DEVICES=$(nvidia-smi -L | awk '{print $2}' | awk -F ':' '{print $1}' | tr '\n' ',')
            export CUDA_VISIBLE_DEVICES
            adapter=$MODEL_PRETRAINED_PATH
        fi
    fi
fi

run() {
    tasks=$1
    pythonm=$2
    if [ -z "$tasks" ]; then
        echo "tasks is empty"
    else
        cd paneval
        $pythonm evalmm/server/run_server.py --port $port --tasks $tasks --checkpoint="$adapter" --output-dir $out_dir $tryrun &>$log_path &
        pid=$!
        sleep 30
        cd ..
        cd ..
        pwd
        echo "begin run client run.sh..." >>$log_path
        bash -x run.sh http://127.0.0.1 $port &
        #nohup bash -x run.sh http://127.0.0.1 5000 &>>$log_path &
        pid1=$!

        cd -
        $pythonm helper.py output $out_dir $pid1 $port $log_path | cat

        kill -9 $pid | cat
        kill -9 $pid1 | cat
    fi
}

run "$tasks" $pythonm
exit 0
