#!/bin/bash
set -ex
mkdir -p /data/log/app/paneval/
mkdir -p /data/log/app/paneval-beat/
mkdir -p /data/log/app/paneval-celery/
mkdir -p /data/log/app/paneval-executor/
mkdir -p /data/log/nginx/paneval/
cp /paneval/deployments/${PANEVAL_DEPLOYMENT_STAGE}/settings.py /paneval/local_settings.py

nginx
poetry run ./manage.py migrate
if [ ! -e ~/.ssh ]; then
    mkdir ~/.ssh
fi
echo $PANEVAL_EXECUTOR_SSH_PRIVATE_KEY | base64 -d | tee ~/.ssh/id_ed25519
chmod 0600 ~/.ssh/id_ed25519
cat <<EOF > /root/.ssh/config
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF
exec supervisord -c /etc/supervisor/supervisord.conf -n
