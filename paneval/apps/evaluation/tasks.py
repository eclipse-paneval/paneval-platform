import json
import logging
import os
import subprocess

from celery import shared_task
from django.conf import settings
from paneval import storage

from . import executor
from .models import SfTaskResult


logger = logging.getLogger(__name__)

g_running = {}

ONLINE_JOB_BATCH_ID = -4


@shared_task
def init_ssh_executor():
    dist_path = '~/online_third_party/'
    flag, sft = _create_online_job()
    if flag == 0 and sft.result["status"] != 1:
        sft.result["status"] = 2
        sft.save()
        cmd = executor.service.online_rsync_to_remote(os.path.join(settings.BASE_DIR, "third_party/online/"), dist_path)
        result = subprocess.run(cmd, capture_output=True, text=True)
        flag = 1
        if result.returncode == 0:
            cmd = executor.service.online_ssh_exe_cmd(
                f"cat>~/online_third_party/conf.json; "
                f"mkdir -p /share/project/eval_results/env; "
                f"mkdir -p {dist_path}mm/env",
            )
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, input=json.dumps(storage.store.get_conf()))
            if result.returncode == 0:
                sync_cmd = executor.service.online_rsync_to_remote(
                    os.path.join(settings.BASE_DIR, "third_party/mm/"),
                    '~/online_third_party/mm/',
                )
                result = subprocess.run(sync_cmd, capture_output=True, text=True)
                ssh_cmd = executor.service.online_ssh_exe_cmd(
                    "bash -x ~/online_third_party/init.sh 2>&1 | tee ~/online_third_party/init.log",
                )
                result = subprocess.run(
                    ssh_cmd,
                    text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if result.returncode == 0:
                    sft.result["status"] = 1
                    sft.save()
                else:
                    logger.error("ssh error, please check!!!, cmd=%r, stderr=%s", ssh_cmd, result.stderr)
            else:
                logger.error("ssh error, please check!!!, cmd=%r, stderr=%s", cmd, result.stderr)


        else:
            logger.error("scp error, please check!!!, cmd=%r, stderr=%s", cmd, result.stderr)
    else:
        return


def _create_online_job():
    batch_id = ONLINE_JOB_BATCH_ID

    try:
        sft = SfTaskResult.objects.get(batch_id=batch_id)
        exp_id = sft.result["exp_id"]
    except SfTaskResult.DoesNotExist:
        exp_id = 'none'

        sft = SfTaskResult.objects.create(
            batch_id = batch_id,
            result = {"exp_id": exp_id}
        )

    sft.result.setdefault("status", 0)
    return 0, sft
