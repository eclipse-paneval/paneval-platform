# How to Build a Conda Enviroment for Evaluation

## Language Model Evaluation Harness
``` shell
$ conda create -n paneval-lmeval python=3.10
# Activate the new created conda env.
$ conda activate paneval-lmeval
$ cd feam-lmeval
$ pip install .
$ conda install conda-pack
$ conda pack -n paneval-lmeval -o conda-full-lmeval.tar.gz
```

## OpenCompass

``` shell
$ conda create -n paneval-opencompass python=3.10
# Activate the new created conda env.
$ conda activate paneval-opencompass
$ cd feam-opencompass
$ pip install .
$ conda install conda-pack
$ conda pack -n paneval-opencompass -o conda-full-opencompass.tar.gz
```


## EvalMM

``` shell
$ conda create -n paneval-evalmm python=3.10
# Activate the new created conda env.
$ conda activate paneval-evalmm
$ git clone https://github.com/eclipse-paneval/paneval.git
$ cd paneval
$ pip install .
$ conda install conda-pack
$ conda pack -n paneval-evalmm -o conda-full-evalmm.tar.gz
```
