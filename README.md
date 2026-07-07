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
   PANEVAL_EXECUTOR_SSH_PUBLIC_KEY='' # cat id_ed25519.pub
   PANEVAL_EXECUTOR_SSH_PRIVATE_KEY='' # cat id_ed25519 | base64
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
