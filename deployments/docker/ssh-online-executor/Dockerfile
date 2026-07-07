FROM ubuntu:22.04
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai  /etc/localtime
RUN echo '#!/bin/bash' | tee /usr/bin/nvidia-smi && chmod +x /usr/bin/nvidia-smi
RUN apt update && apt install -y ca-certificates
RUN apt update && apt install -y apache2-utils nginx openssh-server curl python3-pip tzdata
ADD paneval.conf /etc/nginx/conf.d/
RUN sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN ln -sf /usr/bin/python3 /usr/bin/python && ln -sf /usr/bin/pip3 /usr/bin/pip
RUN sed -i 's/listen \[::\]:80/listen [::]:18080/g' /etc/nginx/sites-available/default && \
    sed -i 's/listen 80/listen 18080/g' /etc/nginx/sites-available/default && \
    sed -i 's/^#\?Port 22/Port 3022/' /etc/ssh/sshd_config
RUN apt install -y rsync
EXPOSE 3022
EXPOSE 8080
ADD run.sh /run.sh
CMD ["bash", "-ex", "/run.sh"]
