# Paneval Platform

Eclipse PanEval evaluation platform (web UI & services).

## Installation

``` shell
poetry install --no-root
```

## Local Development

1. Generate a secret and create `.docker-compose.env`

    ```shell
    $ export PANEVAL_SECRET=$(openssl rand 12 | base64)
    $ cat <<EOF > .docker-compose.env
    MYSQL_ROOT_PASSWORD=$PANEVAL_SECRET
    MYSQL_DATABASE=paneval
    MYSQL_USER=paneval
    MYSQL_PASSWORD=$PANEVAL_SECRET
    EOF
    ```

2. Create `local_settings.py`:

    ```shell
    $ cat <<EOF > local_settings.py
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "HOST": "127.0.0.1",
            "PORT": 13306,
            "NAME": "paneval",
            "USER": "paneval",
            "PASSWORD": "${PANEVAL_SECRET}",
        },
    }


    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://127.0.0.1:16379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        },
    }
    EOF
    ```
2. Use `docker-compose` to start MySQL & Redis & Executor:
   Generate public/private key:
   ```shell
   ssh-keygen -t ed25519 -C "paneval-self-hosted" -f ./id_ed25519
   ```
   Create `.env` and fill required environmental variables:
   ```shell
   PANEVAL_WEB_PORT=8080
   PANEVAL_WEB_BUILD_OUT_DIR=/path/to/frontend-build-output-dir
   PANEVAL_DOCS_BUILD_OUT_DIR=/path/to/docs-build-output-dir/.vitepress/dist
   PANEVAL_EXECUTOR_HTTP_USER=paneval
   PANEVAL_EXECUTOR_HTTP_PASSWD='${PANEVAL_SECRET}'
   PANEVAL_EXECUTOR_SSH_PORT=3022
   PANEVAL_EXECUTOR_SSH_PUBLIC_KEY='' # One key, or multiple keys separated by semicolons/newlines
   PANEVAL_EXECUTOR_SSH_PRIVATE_KEY='' # cat id_ed25519 | base64
   PANEVAL_SSH_EXECUTOR_INSTANCES='' # Multi-host example: root@machine1,root@machine2
   ```
   Start
    ```shell
    docker-compose up -d mysql
    docker-compose up -d redis
    docker-compose up -d executor
    ```

3. Migrate Database Schema

    ```shell
    poetry run ./manage.py migrate
    ```

4. Run server

    ```shell
    poetry run ./manage.py runserver
    ```

5. Run Celery worker

    ```shell
    poetry run celery -A paneval worker -l INFO
    ```

## Prepare Multi-modal Datasets

Use the evalmm Python environment with the
[paneval evaluator](https://github.com/eclipse-paneval/paneval) installed.
This is a separate checkout from `paneval-platform`. Run preparation where
`/share/project` is the executor's shared data mount, with enough space for
both downloaded archives and extracted images.

Docker maps `${PANEVAL_EXECUTOR_DATA_DIR:-./executor-data}` on the host to
`/share/project` in the containers. The prepared data must be on that mount
and accessible to every executor. Creating `/share/project` elsewhere on the
host does not make it visible inside the containers.

Public datasets are downloaded and processed into the shared cache:

``` shell
cd /path/to/paneval
export EVALMM_DATASETS_CACHE_DIR=/share/project/evalmm-cache
mkdir -p "$EVALMM_DATASETS_CACHE_DIR"

# RefCOCO and ARP grounding
python -m evalmm.dataset.data_preprocessor -c tasks/refcoco/refcoco_val.py
python -m evalmm.dataset.data_preprocessor -c tasks/refcoco/refcoco_g_val.py
python -m evalmm.dataset.data_preprocessor -c tasks/refcoco/refcoco_plus_val.py
python -m evalmm.dataset.data_preprocessor -c tasks/arpgrounding/arpgrounding_priority_val.py
python -m evalmm.dataset.data_preprocessor -c tasks/arpgrounding/arpgrounding_attribute_val.py
python -m evalmm.dataset.data_preprocessor -c tasks/arpgrounding/arpgrounding_relation_val.py

# Color bench
python -m evalmm.dataset.data_preprocessor -c tasks/color_bench/color_bench_test.py

# Image VQA (public configs from migration 0002)
python -m evalmm.dataset.data_preprocessor -c tasks/blink/blink_val.py
python -m evalmm.dataset.data_preprocessor -c tasks/cii_bench/cii_bench_test.py
python -m evalmm.dataset.data_preprocessor -c tasks/cmmmu/cmmmu_val.py
python -m evalmm.dataset.data_preprocessor -c tasks/math_vision/math_vision_test.py
python -m evalmm.dataset.data_preprocessor -c tasks/mmvet/mmvet_v2.py
python -m evalmm.dataset.data_preprocessor -c tasks/mmmu/mmmu_val.py
python -m evalmm.dataset.data_preprocessor -c tasks/mmmu_pro/mmmu_pro_standard_test.py
python -m evalmm.dataset.data_preprocessor -c tasks/charxiv/charxiv_val.py
python -m evalmm.dataset.data_preprocessor -c tasks/math_verse/math_verse_testmini.py
python -m evalmm.dataset.data_preprocessor -c tasks/chart_qa/chart_qa_test.py
python -m evalmm.dataset.data_preprocessor -c tasks/cmmu/cmmu.py
python -m evalmm.dataset.data_preprocessor -c tasks/hallusion_bench/hallusion_bench_image.py
python -m evalmm.dataset.data_preprocessor -c tasks/math_vista/math_vista_testmini.py
python -m evalmm.dataset.data_preprocessor -c tasks/ocrbench/ocrbench_test.py
```

Internal datasets from migration 0002 use the configs vendored in this
repository under `third_party/mm/internal/tasks` (see
[third_party/mm/internal/README.md](third_party/mm/internal/README.md)).
They have no download `config` block, so `data_preprocessor` cannot prepare
them. Stage their images and annotations at each config's fixed `data_root`
on the executor data mount, then verify from the same evalmm environment:

``` shell
export PANEVAL_INTERNAL_TASKS_DIR=/path/to/paneval-platform/third_party/mm/internal/tasks

for cfg in \
    vqa/robust/cv_bench/cv_bench_test_uap.py \
    vqa/mmbench/mm_bench_cn.py \
    vqa/mmbench/mm_bench_en.py \
    vqa/science_qa/science_qa.py \
    vqa/seed_bench/seed_bench.py \
    vqa/tdiuc/tdiuc.py \
    vqa/vqa2.0/vqa2.0.py \
    vqa/vqa_cp/vqacp.py; do
    python -c 'import os, sys; from mmengine.config import Config; root = Config.fromfile(sys.argv[1]).dataset.data_root; print("ok     " if os.path.isdir(root) else "MISSING", root)' \
        "$PANEVAL_INTERNAL_TASKS_DIR/$cfg"
done
```

TDIUC also reads `sample_answerkey.csv` under the COCO `data_root`. CV-Bench
UAP uses the legacy `/share/projset/...` path, which must also resolve inside
the executor containers.

## License

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
