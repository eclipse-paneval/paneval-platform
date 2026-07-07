FROM python:3.10

RUN pip install -U pip && \
    pip install -U supervisor poetry && \
    apt update && apt install -y nginx default-libmysqlclient-dev build-essential rsync

ADD deployments/supervisor /etc/supervisor
ADD deployments/logrotate.d/supervisor /etc/logrotate.d/supervisor
ADD deployments/nginx/conf.d /etc/nginx/conf.d
ADD deployments/start.sh /start.sh
ADD . /paneval

WORKDIR /paneval
RUN mkdir /root/.ssh && ssh-keyscan gitee.com >> /root/.ssh/known_hosts

RUN poetry --version && \
    poetry config virtualenvs.options.always-copy true && \
    poetry config virtualenvs.create false

ENV PIP_DEFAULT_TIMEOUT=1000
RUN poetry install --only main --no-root && \
    rm -f /etc/nginx/sites-enabled/default

ENV PANEVAL_DEPLOYMENT_STAGE=test
ENTRYPOINT /bin/sh /start.sh
