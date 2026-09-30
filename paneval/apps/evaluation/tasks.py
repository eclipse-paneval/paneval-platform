import copy
import json
import logging
import os
import subprocess
from typing import Any, Dict, Optional

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from paneval import storage

from . import executor
from .models import SfTaskResult


logger = logging.getLogger(__name__)

ONLINE_JOB_BATCH_ID = -4
_INIT_LOCK_TIMEOUT = 25 * 60
_STATE_CREATE_LOCK_KEY = 'paneval:ssh-executor-state-create'


@shared_task
def init_ssh_executor():
    _refresh_legacy_status()
    for instance in executor.list_instances():
        init_ssh_executor_instance.delay(instance)


@shared_task
def init_ssh_executor_instance(instance: str):
    if instance not in executor.list_instances():
        return
    if executor_instance_ready(instance):
        return

    lock_key = f'paneval:ssh-executor-init:{instance}'
    if not cache.add(lock_key, '1', timeout=_INIT_LOCK_TIMEOUT):
        return

    try:
        if executor_instance_ready(instance):
            return
        if not _update_instance_state(instance, status=2, error='', attempted=True):
            return

        service = executor.get_service(instance)
        dist_path = '~/online_third_party/'
        _run_executor_command(
            instance,
            service.online_rsync_to_remote(
                os.path.join(settings.BASE_DIR, 'third_party/online/'),
                dist_path,
            ),
        )
        _run_executor_command(
            instance,
            service.online_ssh_exe_cmd(
                f'cat>~/online_third_party/conf.json; '
                f'mkdir -p /share/project/eval_results/env; '
                f'mkdir -p {dist_path}mm/env',
            ),
            input=json.dumps(storage.store.get_conf()),
        )
        _run_executor_command(
            instance,
            service.online_rsync_to_remote(
                os.path.join(settings.BASE_DIR, 'third_party/mm/'),
                '~/online_third_party/mm/',
            ),
        )
        _run_executor_command(
            instance,
            service.online_ssh_exe_cmd(
                'bash -x ~/online_third_party/init.sh 2>&1 | '
                'tee ~/online_third_party/init.log',
            ),
        )
        _update_instance_state(instance, status=1, error='')
    except Exception as exc:
        logger.error('failed to initialize executor instance %s', instance, exc_info=True)
        _update_instance_state(
            instance,
            status=0,
            error=str(exc),
            attempted=True,
        )
    finally:
        cache.delete(lock_key)


def executor_instance_ready(instance: Optional[str]) -> bool:
    try:
        canonical_instance = executor.get_service(instance).instance
    except executor.ExecutorInstanceError:
        return False

    row = _online_job_row()
    if row is None:
        return False
    instances = (row.result or {}).get('instances') or {}
    return (instances.get(canonical_instance) or {}).get('status') == 1


def _run_executor_command(instance: str, command, **kwargs):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        **kwargs,
    )
    if result.returncode == 0:
        return result

    detail = (result.stderr or result.stdout or '').strip()
    raise executor.ExecutorUnreachable(
        f'executor instance {instance} command failed with exit code '
        f'{result.returncode}: {detail}'
    )


def _online_job_row() -> Optional[SfTaskResult]:
    rows = SfTaskResult.objects.filter(
        batch_id=ONLINE_JOB_BATCH_ID,
    ).order_by('pk')
    row = rows.first()
    if row is not None and rows.count() > 1:
        logger.warning(
            'multiple SfTaskResult rows found for online executor state; using pk=%s',
            row.pk,
        )
    return row


def _ensure_online_job_row() -> Optional[SfTaskResult]:
    row = _online_job_row()
    if row is not None:
        return row
    if not cache.add(_STATE_CREATE_LOCK_KEY, '1', timeout=60):
        return None

    try:
        with transaction.atomic():
            row = SfTaskResult.objects.select_for_update().filter(
                batch_id=ONLINE_JOB_BATCH_ID,
            ).order_by('pk').first()
            if row is None:
                row = SfTaskResult.objects.create(
                    batch_id=ONLINE_JOB_BATCH_ID,
                    result={
                        'exp_id': 'none',
                        'status': 0,
                        'instances': {},
                    },
                )
            return row
    finally:
        cache.delete(_STATE_CREATE_LOCK_KEY)


def _refresh_legacy_status() -> None:
    with transaction.atomic():
        row = SfTaskResult.objects.select_for_update().filter(
            batch_id=ONLINE_JOB_BATCH_ID,
        ).order_by('pk').first()
        if row is None:
            return

        result: Dict[str, Any] = copy.deepcopy(row.result or {})
        instances = result.get('instances') or {}
        status = int(all(
            (instances.get(item) or {}).get('status') == 1
            for item in executor.list_instances()
        ))
        if result.get('status') == status:
            return
        result['status'] = status
        row.result = result
        row.save(update_fields=['result'])


def _update_instance_state(
        instance: str,
        status: int,
        error: str,
        attempted: bool = False,
) -> bool:
    if _ensure_online_job_row() is None:
        return False

    now = timezone.now().isoformat()
    with transaction.atomic():
        row = SfTaskResult.objects.select_for_update().filter(
            batch_id=ONLINE_JOB_BATCH_ID,
        ).order_by('pk').first()
        if row is None:
            return False

        result: Dict[str, Any] = copy.deepcopy(row.result or {})
        result.setdefault('exp_id', 'none')
        instances = result.setdefault('instances', {})
        state = instances.setdefault(instance, {})
        state.update({
            'status': status,
            'updated_at': now,
            'error': error,
        })
        if attempted:
            state['last_attempt_at'] = now

        configured_instances = executor.list_instances()
        result['status'] = int(all(
            (instances.get(item) or {}).get('status') == 1
            for item in configured_instances
        ))
        row.result = result
        row.save(update_fields=['result'])
    return True
