#!/bin/bash
work_dir=`dirname $0`
work_dir=`cd $work_dir;pwd`
cd $work_dir

mkdir -p ~/.cache/evalmm
ln -s $DATASETS_DATASET_DOWNLOAD_PATH  ~/.cache/evalmm/datasets

apt-get update
apt-get install -y psmisc
apt install -y libgl1-mesa-glx
apt-get install lsof
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
if [[ ! -e /root/miniconda3 ]];
then
    CONDA_TAR_GZ=$(find $CONDA_DATASET_DOWNLOAD_PATH -name 'conda-full-evalmm.tar.gz')
    tar -zxf $CONDA_TAR_GZ -C /root/miniconda3
fi
