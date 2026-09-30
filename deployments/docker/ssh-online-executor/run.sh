#!/bin/bash
set -eu

# Create HTTP Basic Authentication.
htpasswd -c -b /etc/nginx/.htpasswd $PANEVAL_EXECUTOR_HTTP_USER $PANEVAL_EXECUTOR_HTTP_PASSWD

# Initial SSH.
mkdir -p ~/.ssh && \
    printf '%s\n' "$PANEVAL_EXECUTOR_SSH_PUBLIC_KEY" | tr ';' '\n' > ~/.ssh/authorized_keys && \
    chmod 600 ~/.ssh/authorized_keys && \
    mkdir -p /run/sshd && chmod 0755 /run/sshd

mkdir -p /share/project/eval_results/
/usr/sbin/nginx
if [ ! -e /var/run/sshd ]; then
    mkdir -p /var/run/sshd
    chmod 755 /var/run/sshd
fi
exec /usr/sbin/sshd -D
