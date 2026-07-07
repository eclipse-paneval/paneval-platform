"""Celery tasks for CEM."""
import collections
import io
import json
import os
import subprocess
import traceback
import threading
import time

from dataclasses import dataclass
from typing import List, Any, Optional, Dict, IO, Set
import uuid

from celery import shared_task
from celery.signals import task_failure
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.core.cache import cache
from django.utils import timezone

from ...storage import store
from ..evaluation import executor
from ..evaluation.models import Evaluation, Dataset,  CvTaskResult, SfTaskResult, ImageData
from ..evaluation.tasks import ONLINE_JOB_BATCH_ID
from ..user.models import User
from . import models
from .utils import copy_tokenizer_to, get_nlp_scenario_options, merge_lbx_batch
from paneval import storage


logger = get_task_logger(__name__)


@dataclass
class SyncJob:
   storage_key: str
   done: bool = False
   user_model: bool = False
   sync_id: Optional[str] = None


@task_failure.connect()
def celery_task_failure_email(**kwargs):
    from django.core.mail import mail_admins
    import socket

    subject = "[{queue_name}@{host}] Error: Task {sender.name} ({task_id}): {exception}".format(  # noqa
        queue_name="celery",  # `sender.queue` doesn't exist in 4.1?
        host=socket.gethostname(),
        **kwargs
    )
    message = """Task {sender.name} with id {task_id} raised exception:
{exception!r}Task was called with args: {args} kwargs: {kwargs}.The contents of the full traceback was:{einfo}
    """.format(
        **kwargs
    )
    mail_admins(subject, message)


@dataclass
class RunUnit:
    scenario_entry_point: str
    task_id: str
    dataset_id: str


@dataclass
class DAGContext:
    evaluation_id: int
    batch_id: int
    dataset_id: int
    dag_id: str
    run_unit: RunUnit
    disturbance: str
    disturbance_opts: dict
    pending: bool = True

    def is_cancelled(self) -> bool:
        return is_batch_id_cancelled(self.batch_id)


def is_batch_id_cancelled(batch_id: int) -> bool:
    return is_batch_cancelled(models.Batch.objects.get(pk=batch_id))


def is_batch_cancelled(batch: models.Batch) -> bool:
    return batch.status in [
        models.Batch.Status.CANCEL,
    ]


def create_nlp_dags(
        run_batch: models.Batch, datasets: Optional[List[int]] = None,
        include_robustness=True,
) -> bool:
    new_dags_created = False
    if run_batch.dags_ready:
        return new_dags_created

    eva = Evaluation.objects.get(pk=run_batch.evaluation_id)
    ds_queryset = Dataset.objects.filter(pk__in=datasets or eva.datasets)
    dags_delayed_tasks: Dict[str, Dict[str, Any]] = collections.defaultdict(dict)
    options = get_nlp_scenario_options(eva, dry_run=run_batch.dry_run)
    for item in ds_queryset:
        dags_delayed_tasks[item.package]['dags_ready'] = False
        dags_delayed_tasks[item.package]['options'] = {
            'server_url': options.server_url,
            'model': options.model,
            'extras': options.extras,
        }
        dags_delayed_tasks[item.package].setdefault('tasks', collections.defaultdict(list))
        dags_delayed_tasks[item.package]['tasks'][item.feam_scenario].append({
            'evaluation_id': run_batch.evaluation_id,
            'batch_id': run_batch.pk,
            'scenario_entry_point': item.feam_scenario,
            'feam_task_id': item.feam_task_id,
            'dataset_id': item.pk,
        })

    with transaction.atomic():
        run_batch.include_robustness = include_robustness
        run_batch.save()
        if datasets is not None:
            models.DAG.objects.filter(
                ~Q(dataset_id__in=datasets),
                ~Q(status__in=models.Batch.SUCCESS_STATUSES),
                batch_id=run_batch.pk,
            ).update(
                deleted_at=timezone.now(),
            )
            if not include_robustness:
                models.DAG.objects.filter(
                    ~Q(disturbance=''),
                    ~Q(status__in=models.Batch.SUCCESS_STATUSES),
                    batch_id=run_batch.pk,
                ).update(
                    deleted_at=timezone.now(),
                )

        run_batch.dags_ready = False
        run_batch.dags_delayed_tasks = dags_delayed_tasks
        if new_dags_created:
            run_batch.status = models.Batch.Status.MODIFIED
        run_batch.save()
        return new_dags_created


@shared_task
def attempt_resume(batch_id: int):
    running_dag = models.DAG.objects.filter(
        batch_id=batch_id,
        status=models.Batch.Status.RUNNING,
        deleted_at=None,
    ).first()

    if running_dag is None:
        return

    models.DAG.objects.filter(
        ~Q(status=models.Batch.Status.SUCCESS),
        batch_id=batch_id,
        deleted_at=None,
    ).update(
        status=models.Batch.Status.PENDING,
    )
    batch = models.Batch.objects.get(pk=batch_id)
    run_on_executor.delay(batch_id, batch.try_sequence)


def watch_batch_timeout(batch_id: int, timeout=1800):
    on_batch_timeout.apply_async(
        args=(batch_id,),
        countdown=timeout,
    )


@shared_task()
def on_batch_timeout(batch_id: int):
    batch = models.Batch.objects.get(
        pk=batch_id,
    )
    if batch.status not in [models.Batch.Status.RUNNING.value, models.Batch.Status.PENDING.value]:
        logger.info("BATCH %d has completed with status %r", batch.pk, batch.status)
        return

    delta = timezone.now() - batch.updated_at
    if delta.seconds > 3600:
        logger.warn("Batch %d is timeout with status %r.", batch.pk, batch.status)
        on_error.delay(batch_id, models.Batch.FailureKind.SYSTEM, "timeout")
        return

    if delta.seconds > 1800:
        logger.warn(
            "Batch %d is inactive in %d seconds with status %r, attempt to resume",
            batch.pk, delta.seconds, batch.status,
        )
        attempt_resume.delay(batch_id)
        return

    logger.warn(
        "Batch %d is still active in %d seconds with status %r",
        batch.pk, delta.seconds, batch.status,
    )
    watch_batch_timeout(batch_id)


@shared_task()
def on_error(batch_id, failure_kind=None, failure_details=None):
    """Handling error."""
    cancel_batch(batch_id, failure_kind=failure_kind, failure_details=failure_details)


def cancel_batch(
        batch_id,
        status: models.Batch.Status = models.Batch.Status.FAILURE,
        failure_kind: Optional[models.Batch.FailureKind] = None,
        failure_details: Optional[str] = None,
):
    batch = models.Batch.objects.get(pk=batch_id)
    with transaction.atomic():
        eva = Evaluation.objects.get(pk=batch.evaluation_id)
        if eva.domain == Evaluation.Domain.MULTI:
            # 如果任务被中途停掉或者啥的，没跑的程序都弄成取消。
            items = CvTaskResult.objects.filter(
                ~Q(status__in=[-1, 1]), batch_id = batch_id,
                deleted_at=None,
            )
            for item in items:
                item.status = 3
                item.save()
        elif eva.domain in Evaluation.Domain.NLP:
            models.DAG.objects.filter(
                batch_id=batch_id,
                status=models.Batch.Status.RUNNING,
                deleted_at=None,
            ).update(
                status=status,
                updated_at=timezone.now(),
            )

            models.DAG.objects.filter(
                batch_id=batch_id,
                status=models.Batch.Status.PENDING,
            ).update(
                status=models.Batch.Status.CANCEL,
                updated_at=timezone.now(),
            )

        models.Batch.objects.filter(pk=batch_id).update(
            status=status,
            updated_at=timezone.now(),
            failure_kind=failure_kind,
            failure_details=failure_details,
        )
        if eva.sence == Evaluation.Sence.API.value:
            kill_online.apply_async(
                args=(f"{batch_id}.{batch.try_sequence}",),
                countdown=10
            )
        elif batch.joint_job_id:
            executor.service.stop_job(batch.joint_job_id)
    notify_status.delay(batch_id)


@shared_task()
def kill_online(batch_id):
    try:
        cmd = executor.service.online_ssh_exe_cmd(f"bash ~/online_third_party/kill.sh {batch_id}")
        subprocess.run(cmd)
    except:
        traceback.print_exc()


@shared_task()
def run_on_executor(batch_id: int, try_sequence: int):
    try:
        notify_status(batch_id)
    except Exception:
        logger.error("failed to notify status changed", exc_info=True)

    watch_batch_timeout(batch_id)

    effected_rows = models.Batch.objects.filter(
        pk=batch_id,
        try_sequence=try_sequence,
    ).update(
        status=models.Batch.Status.PREPARING,
        updated_at=timezone.now(),
    )
    if effected_rows == 1:
        notify_status.delay(batch_id)
        start_sync_model.delay(batch_id, try_sequence)


def sync_dir(path, key):
    for filename in os.listdir(path):
        fkey = os.path.join(key, filename)
        fpath = os.path.join(path, filename)
        if os.path.isdir(fpath):
            sync_dir(fpath, fkey)
            continue
        for i in range(3):
            try:
                with open(fpath, 'rb') as f:
                    logger.info("sending file %s to %s", fpath, fkey)
                    store.upload(fkey, f)
                    break
            except Exception as e:
                traceback.print_exc()
                logger.info("sending file error", fpath, fkey, i)
                if i == 2:
                    raise e
                time.sleep(50)


@shared_task
def start_sync_model(batch_id: int, try_sequence: int):
    batch = models.Batch.objects.get(pk=batch_id)
    if batch.try_sequence != try_sequence:
        return

    eva = Evaluation.objects.get(pk=batch.evaluation_id)
    try:
        if eva.domain == Evaluation.Domain.NLP:
            thirdy_party = os.path.join(settings.BASE_DIR, "third_party/nlp")
        elif eva.domain == Evaluation.Domain.MULTI:
            thirdy_party = os.path.join(settings.BASE_DIR, "third_party/mm")
        else:
            raise RuntimeError(f'unsupported domain {eva.domain}')
        if eva.sence == Evaluation.Sence.API.value:
            batch.model_storage_url = f'api/eval-{eva.pk}/batch-{batch.pk}'
            batch.save()

        model_storage_url = batch.model_storage_url

        if eva.tokenizer is not None:
            key = os.path.join(model_storage_url, "__paneval__", "tokenizer.json")
            store.upload(key, json.dumps(eva.tokenizer))

        nlp_packages: List[str] = []

        if eva.domain == Evaluation.Domain.NLP:
            base_key = os.path.join(model_storage_url, "__paneval__")
            nlp_packages = _upload_contexts_to_model(batch, base_key)
            _upload_datasets_results_to_model(batch, base_key)
            _upload_material_to_model_storage(eva, model_storage_url, thirdy_party, nlp_packages, "__paneval__")
            if eva.sence == Evaluation.Sence.API.value:
                _upload_material_to_model_storage(eva, model_storage_url, 'third_party/online', [], '__online__')
        if eva.pretrained_tokenizer_id:
            copy_tokenizer_to(
                eva.pretrained_tokenizer_id,
                os.path.join(model_storage_url, "__paneval__", 'tokenizer'),
            )
        if batch.status != models.Batch.Status.CANCEL:
            if eva.domain == Evaluation.Domain.MULTI:
                datas = []
                data = merge_lbx_batch(batch)
                for i in range(len(data)):
                    cur = None
                    try:
                        cur = CvTaskResult.objects.get(
                            batch_id=batch_id,
                            cv_id=data[i]["cv_id"],
                            idx=i,
                            deleted_at=None,
                        )
                    except CvTaskResult.DoesNotExist:
                        pass
                    if cur is not None:
                        cur_data = {"id": cur.pk, "data": data[i], "status": cur.status}
                        datas.append(cur_data)
                items = CvTaskResult.objects.filter(~Q(status=1),
                        batch_id = batch.pk, cv_id=-1).order_by("idx")
                lbx = []
                for item in items:
                    lbx.append({"ret": 0, "property": item.result_json["property"]})
                data = {
                    "eva_name": eva.name,
                    "batch_id": batch_id,
                    "try_run": batch.dry_run,
                    "data": datas,
                    "lbx": lbx,
                    "online_property": eva.online_property,
                }
                s = json.dumps(data, indent = 2, ensure_ascii = False)
                key = os.path.join(model_storage_url, "__paneval__", "config.json")
                store.upload(key, s)

        model_sync_id = None

        sync_jobs = [SyncJob(storage_key=batch.model_storage_url, user_model=True, sync_id=model_sync_id)]
        if eva.domain in settings.STORAGE_DATASETS:
            for _, conf in settings.STORAGE_DATASETS[eva.domain].items():
                sync_jobs.append(SyncJob(
                   storage_key=conf['STORAGE_KEY'],
                    sync_id=conf['DOWNLOAD_ID'],
                ))
        if eva.sence == Evaluation.Sence.API.value:
            on_sync_done = run_online.s(batch_id=batch_id, try_sequence=try_sequence)
        else:
            raise RuntimeError(f'unsupported sence {eva.sence}')
        start_syncing.delay(
            sync_jobs,
            on_error.s(batch_id=batch_id, failure_kind=models.Batch.FailureKind.SYSTEM),
            on_sync_done,
        )
    except Exception as e:
        on_error.delay(batch_id, models.Batch.FailureKind.SYSTEM, str(e))
        raise


def _upload_contexts_to_model(batch: models.Batch, base_key: str) -> List[str]:
    contexts_by_package = _create_dag_contexts(batch)
    for package, contexts in contexts_by_package.items():
        data: List[Dict[str, Any]] = [
            dict(
                evaluation_id=x.evaluation_id,
                batch_id=x.batch_id,
                dataset_id=x.dataset_id,
                dag_id=x.dag_id,
                disturbance=x.disturbance,
                disturbance_opts=x.disturbance_opts,
                pending=x.pending,
                run_unit=dict(
                    scenario_entry_point=x.run_unit.scenario_entry_point,
                    task_id=x.run_unit.task_id,
                    dataset_id=x.run_unit.dataset_id,
                ),
            )
            for x in contexts
        ]

        s = json.dumps(data, indent=2)
        key = os.path.join(base_key, f'{package}-all-ctxs.json')
        logger.info("uploading context to %s, context: %s", key, s)
        store.upload(key, s)

        contexts_by_task: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
        for item in data:
            task_id = item['run_unit']['task_id']
            contexts_by_task[task_id].append(item)

        for task_id, ctxs in contexts_by_task.items():
            key = os.path.join(base_key, f'{package}-{task_id}-contexts.json')
            s = json.dumps(ctxs, indent=2)
            logger.info("uploading context to %s, context: %s", key, s)
            store.upload(key, s)
    packages = list(contexts_by_package.keys())
    key = os.path.join(base_key, f'dags-delayed-tasks.json')
    s = json.dumps(
        {
            pkg: detail
            for pkg, detail in batch.dags_delayed_tasks.items()
            if not detail['dags_ready']
        },
        indent=2,
    )
    logger.info('uploading dags delayed tasks to %s, content: %s', key, s)
    store.upload(key, s)
    packages.extend(
        pkg for pkg in batch.dags_delayed_tasks.keys()
    )
    return list(set(packages))


def _create_dag_contexts(batch: models.Batch) -> Dict[str, List[DAGContext]]:
    kwargs = {}
    kwargs.update(is_objective=True)
    datasets: Dict[int, Dataset] = {
        x.pk: x
        for x in Dataset.objects.filter(
                ~Q(feam_scenario=''), **kwargs,
        ).order_by("id").all()
    }
    dags = models.DAG.objects.defer("result").filter(
        batch_id=batch.pk,
        deleted_at=None,
    ).order_by("id")

    contexts: Dict[str, List[DAGContext]] = collections.defaultdict(list)
    subjective_contexts: Dict[str, List[DAGContext]] = collections.defaultdict(list)
    packages: Set[str] = set()
    for dag in dags:
        dataset = datasets[dag.dataset_id]
        ctx = DAGContext(
            batch_id=batch.pk,
            evaluation_id=batch.evaluation_id,
            dataset_id= dag.dataset_id,
            dag_id=dag.dag_id,
            disturbance=dag.disturbance,
            disturbance_opts=dag.disturbance_opts,
            pending=dag.status == models.Batch.Status.PENDING,
            run_unit=RunUnit(
                scenario_entry_point=dataset.feam_scenario,
                task_id=dataset.feam_task_id,
                dataset_id=dag.run_entry,
            ),
        )
        packages.add(dataset.package)
        if dataset.is_objective:
            contexts[dataset.package].append(ctx)
        else:
            subjective_contexts[dataset.package].append(ctx)

    results: Dict[str, List[DAGContext]]  = {}
    for package in packages:
        results[package] = contexts[package] + subjective_contexts[package]
    if len(results) == 0 and not batch.dags_delayed_tasks:
        raise RuntimeError(f'empty dags for {batch.pk}')
    return results



def _upload_datasets_results_to_model(batch: models.Batch, base_key: str):
    queryset = models.DatasetResult.objects.filter(batch_id=batch.pk).all()
    for item in queryset:
        name = f'batch-{item.batch_id}-dataset-{item.dataset_id}-disturbance-{item.disturbance}.json'
        key = os.path.join(base_key, executor.service.get_result_name(batch.try_sequence, name))
        logger.info(f'Uploading dataset result to the model path {key}...')
        ds_ret = {
            'batch_id': item.batch_id,
            'scenario_entry_point': item.scenario_entry_point,
            'dataset_id': item.dataset_id,
            'result': item.result,
            'avg': item.avg_elapsed,
            'max': item.max_elapsed,
            'total': item.total_instances,
            'started_at': item.started_at,
            'stopped_at': item.stopped_at,
        }
        store.upload(key, json.dumps(ds_ret))


@shared_task
def start_syncing(jobs: List[SyncJob], on_error, callback):
    # 忽略下载服务，触发手动下载
    download_job = [job for job in jobs if job.user_model][0]
    try:
        for job in jobs:
            if job.sync_id is None:
                job.sync_id = str(uuid.uuid4())
            src = storage.store.full_uri(job.storage_key).rstrip("/") + "/" # Source with slash ended to copy its content
            dst_path = os.path.join(executor.service.model_root, job.sync_id)
            output = subprocess.check_output(
                executor.service.online_rsync_to_remote(src, dst_path),
            )
            logger.info(f"rsync output: %s", output)
    except subprocess.CalledProcessError as e:
        on_error.delay(failure_details=f'{e} >>> {e.output}')
    except Exception as e:
        on_error.delay(failure_details=str(e))
    else:
        callback.delay(download_job=download_job)
    return


def _upload_material_to_model_storage(
        eva: Evaluation,
        model_storage_url: str,
        third_party: str,
        nlp_packages: List[str],
        dist: str = '__paneval__',
):
    if not third_party.startswith('/'):
        third_party = os.path.join(settings.BASE_DIR, third_party)

    for filename in os.listdir(third_party):
        key = os.path.join(model_storage_url, dist, filename)
        path = os.path.join(third_party, filename)
        if filename == "bootstrap.sh":
            if eva.domain == Evaluation.Domain.NLP:
                f = _append_feam_script(
                    nlp_packages,
                    path,
                )
                logger.info("sending %s to %s", filename, key)
                store.upload(key, f)
                continue

        if os.path.isdir(path):
            sync_dir(path, key)
            continue

        with open(path, 'rb') as f:
            logger.info("sending %s to %s", filename, key)
            store.upload(key, f)


@shared_task
def run_online(batch_id: int, try_sequence: int, download_job: SyncJob):
    batch = models.Batch.objects.get(pk=batch_id)
    if batch.try_sequence != try_sequence or batch.status == models.Batch.Status.CANCEL:
        return
    eva = Evaluation.objects.get(pk=batch.evaluation_id)
    environ = _build_environ(batch, eva, download_job)
    try:
        sft = SfTaskResult.objects.get(batch_id=ONLINE_JOB_BATCH_ID)
        if sft.result["status"] != 1:
            on_error.delay(batch.pk, models.Batch.FailureKind.SYSTEM, "online job error")
            return
        port = 0
        tee_output = os.path.join(executor.service.job_root, f'env/log.{str(batch.pk)}.txt')
        if eva.domain == Evaluation.Domain.NLP:
            src = batch.model_storage_url + "/"
            dst = os.path.join(executor.service.model_root, "online", "batch_" + str(batch.pk) + "." + str(batch.try_sequence))

            batch.status = models.Batch.Status.RUNNING.value
            environ['FEAM_VENV'] = os.path.join(executor.service.job_root, f'env/venv.{batch.pk}')
            model_path = environ['MODEL_PATH']
            inp = '\n'.join([f'export {key}={val}' for key, val in environ.items()])
            cmd = executor.service.online_ssh_exe_cmd(
                f"bash -x {model_path}/__online__/run.sh {str(batch.pk)} {src} {dst} "
                f"{executor.service.get_log_path(batch.pk, 'app', batch.try_sequence)} "
                f"{executor.service.get_log_path(batch.pk, 'eval', batch.try_sequence)} 2>&1 | "
                f"tee {tee_output}")
        elif eva.domain == Evaluation.Domain.MULTI:
            datas = []
            data = merge_lbx_batch(batch)
            for i in range(len(data)):
                cur = None
                try:
                    cur = CvTaskResult.objects.get(
                        batch_id=batch.pk,
                        cv_id=data[i]["cv_id"],
                        idx=i,
                        deleted_at=None,
                    )
                except CvTaskResult.DoesNotExist:
                    pass
                if cur is not None:
                    cur_data = {"id": cur.pk, "data": data[i], "status": cur.status}
                    datas.append(cur_data)
            items = CvTaskResult.objects.filter(~Q(status=1),
                    batch_id = batch.pk, cv_id=-1).order_by("idx")
            lbx = []
            for item in items:
                lbx.append({"ret": 0, "property": item.result_json["property"]})
            data = {
                "eva_name": eva.name,
                "batch_id": batch.pk,
                "try_run": batch.dry_run,
                "data": datas,
                "lbx": lbx,
                "url": eva.url,
                "model_name": eva.online_model_name,
                "api_key": eva.online_api_key,
                "online_property": eva.online_property,
                'evals': '\n'.join([f'export {key}={val}' for key, val in environ.items()]),
            }
            inp = json.dumps(data, indent=2, ensure_ascii=False)
            port = online_port(batch)

            fenv_dir=f"/share/project/mmenv/{batch.pk}.{batch.try_sequence}"
            subprocess.run(executor.service.online_ssh_exe_cmd(f"mkdir {fenv_dir}"))
            cmd = executor.service.online_rsync_to_remote(
                os.path.join(settings.BASE_DIR, "third_party/mm/"),
                f"{fenv_dir}/__paneval__",
            )
            subprocess.run(cmd, capture_output=True, text=True)
            cmd = executor.service.online_ssh_exe_cmd(
                f"bash -x ~/online_third_party/mm.sh {batch.pk}.{batch.try_sequence} "
                f"{executor.service.get_log_path(batch.pk, 'app', batch.try_sequence)} "
                f"\"{executor.service._get_prefix(batch.try_sequence)}\" {port} 2>&1 | "
                f"tee {tee_output}")
        else:
            raise RuntimeError(f'unsupported domain {eva.domain}')
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process.stdin.write(inp.encode())
        process.stdin.close()
        threading.Thread(target=wait_process, args=(process, port)).start()
        batch.joint_job_id = str(process.pid)
        batch.save()
        watch_batch.apply_async(
            args=(batch.pk,),
            countdown=60,
    )
    except SfTaskResult.DoesNotExist:
        traceback.print_exc()
        on_error.delay(batch.pk, models.Batch.FailureKind.SYSTEM, "online job does not exist")


def wait_process(process, port = 0):
    process.wait()


def online_status(pid, eva: Evaluation):
    job = {}
    if eva.domain == Evaluation.Domain.NLP:
        cmd = executor.service.online_ssh_exe_cmd(f"ps -ef | grep 'run.sh {pid}' | grep -v 'grep'| cat")
    else:
        cmd = executor.service.online_ssh_exe_cmd(f"ps -ef | grep 'mm.sh {pid}' | grep -v 'grep' | cat")
    result = subprocess.run(cmd, capture_output = True)
    res = None
    if result.returncode == 0:
        res = result.stdout.decode()
        if res is None or res == "":
            job["status"] = "Succeed"
        else:
            job["status"] = "Running"
    else:
        job["status"] = "Running"
    logger.info("= = testdebug, cmd=%s, res=%s, retcode=%d, job=%r", cmd, res, result.returncode, job)
    return job


def online_port(batch: models.Batch) -> str:
    cmd = executor.service.online_ssh_exe_cmd(
        'python -c "import socket;sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM);sock.bind((\'127.0.0.1\', 0));port = sock.getsockname()[1];sock.close();print(port)"',
    )
    result = subprocess.run(cmd, capture_output=True)
    res = result.stdout.decode()
    logger.info("online_port res: %s", res)
    if not (res is None or res == ""):
        return res.strip()
    return '0'


def _append_feam_script(packages: List[str], path: str) -> IO:
    buf = io.BytesIO()
    with open(path, 'rb') as f:
        buf.write(f.read())

    scripts: List[str] = [
        "pushd $THIRD_PARTY",
    ]
    for package in packages:
        scripts.append(f'bash -ex run_prepare.sh {package}')

    for package in packages:
        if package == 'harness':
            scripts.append(f"bash -ex run_feam.sh {package} 4")
        else:
            scripts.append(f"bash -ex run_feam.sh {package}")
    scripts.append('popd')
    buf.write('\n'.join(scripts).encode('utf8'))
    buf.seek(0)
    return buf


def _build_environ(batch: models.Batch, eva: Evaluation, download_job: SyncJob) -> Dict[str, str]:
    remote_url = eva.url
    if eva.domain == eva.Domain.NLP:
        dt = Dataset.objects.filter(pk__in=eva.datasets).first()
        if dt is not None:
            if dt.package == 'opencompass':
                remote_url = _trim_chat_completions(remote_url)
    default_gen_kwargs = ''
    environ = {
        'DRY_RUN_BATCH': '1' if batch.dry_run else '0',
        'EVAL_SENCE': eva.sence,
        'REMOTE_API': remote_url,
        'RUNNING_BATCH_ID': str(batch.pk),
        'EVALUATION_MODEL_NAME': eva.online_model_name if eva.online_model_name else eva.name,
        'EVALUATION_MODEL_TYPE': eva.model_type,
        "EVALUATION_GEN_KWARGS":eva.model_gen_kwargs if eva.model_gen_kwargs else default_gen_kwargs,
    }
    if eva.tokenizer and 'tokenizer_name' in eva.tokenizer:
        environ['EVALUATION_MODEL_TOKENIZER'] = eva.tokenizer["tokenizer_name"]
    else:
        environ['EVALUATION_MODEL_TOKENIZER'] = ''
    environ.update({k.upper(): v for k, v in eva.environ_vars.items()})
    environ.setdefault('OPENAI_API_KEY', eva.online_api_key or '__no_api_key__')
    assert download_job.sync_id is not None
    return executor.service.build_environ_vars(
        download_job.sync_id,
        batch.pk,
        environ=environ,
        domain=eva.domain,
        try_sequence=batch.try_sequence,
    )


@shared_task()
def watch_batch(batch_id: int):
    from ..evaluation.utils import get_subjective_tasks

    batch = models.Batch.objects.get(pk=batch_id)
    eva = Evaluation.objects.get(pk=batch.evaluation_id)
    success_status = models.Batch.Status.SUCCESS

    if len(get_subjective_tasks(eva)) > 0 and not batch.dry_run:
        success_status = models.Batch.Status.DONE_INFERENCE


    if is_batch_cancelled(batch):
        return
    try:
        job = online_status(int(batch.pk), eva)
        if not batch.dags_ready:
            _prepare_dags(batch, batch.try_sequence)

        results: Optional[Dict[str, Any]] = executor.service.load_batch_status(batch_id, batch.try_sequence)
        logger.info(f'[batch_id={batch_id}] Results: %s', json.dumps(results, indent=2))
    except Exception as e:
        # on_error.delay(batch_id, models.Batch.FailureKind.SYSTEM, str(e))
        # raise
        logger.warn(f"exception on watch job, {str(e)}, batch_id={batch_id}, "
            f"eval_id={batch.evaluation_id},"
            f"status={batch.status}")
        watch_batch.apply_async(
            args=(batch_id,),
            countdown=30,
        )
        return

    all_dags_successed = False
    if results is not None:
        if batch.status != results['status']:
            new_status = results['status']

        if eva.domain == Evaluation.Domain.MULTI:
            tempF = True
            for k, v in results["data"].items():
                ctr = CvTaskResult.objects.get(id=k)

                data = ctr.result_json
                data["data"] = v
                # 如果任务被中途停掉或者啥的，没跑的程序都弄成取消。
                if job['status'] == "Cancelled" or job['status'] == "Failed":
                    if ctr.status != 1 and ctr.status != -1:
                        ctr.status = 3
                        ctr.save()
                elif ctr.status != v["ret"]:
                    ctr.result_json = data
                    ctr.status = v["ret"]
                    ctr.save()
                    # 如果是多模态，try_run需要保存图片到 storage
                    if eva.domain == Evaluation.Domain.MULTI:
                        if batch.dry_run:
                            if v["ret"] == 1:
                                for item in v["data"]:
                                    if "md5" in item:
                                        try:
                                            ImageData.objects.get(md5=item["md5"])
                                        except ImageData.DoesNotExist:
                                            r = requests.get(
                                                executor.service.result["serving_host"] + "imgdata/" + item["md5"],
                                                headers = {},
                                                auth=executor.service._get_serving_basic())
                                            ImageData.objects.create(md5=item["md5"], data=r.content)
                if ctr.status != 1:
                    tempF = False
            # 鲁棒性
            if "lbx" in results and len(results["lbx"]) > 0:
                for item in results["lbx"]:
                    try:
                        cur = CvTaskResult.objects.get(batch_id=batch_id, idx=item["property"]["idx"], cv_id=-1, deleted_at=None)
                    except CvTaskResult.DoesNotExist:
                        cur = CvTaskResult.objects.create(batch_id=batch_id, idx=item["property"]["idx"], cv_id=-1,
                                                          result_json=item)
                    if cur.status != item["ret"]:
                        cur.status = item["ret"]
                        cur.result_json = item
                        cur.save()
                    if cur.status != 1:
                        tempF = False
                if tempF and results['status'] == "S":
                    all_dags_successed = True
            elif tempF and results['status'] == "S":
                all_dags_successed = True
        elif eva.domain in [Evaluation.Domain.NLP]:
            dags_status: List[Dict[str, Any]] = results['dags']
            try:
                all_dags_successed = _handle_joint_dags(batch, batch.try_sequence, dags_status)
            except Exception as e:
                on_error.delay(batch_id, models.Batch.FailureKind.SYSTEM, str(e))

    batch_results = save_batch_results(batch)
    batch.results = batch_results
    batch.updated_at = timezone.now()
    #
    #    // Pending state
    #    Pending State = 0
    #    // Running state
    #    Running State = 1
    #    // Succeed state
    #    Succeed State = 2
    #    // Failed state
    #    Failed State = 3
    #    // Cancelled state
    #    Cancelled State = 4
    #    // Starting state
    #    Starting State = 5
    #
    if job['status'] in ['Cancelled', 'Failed']:
        # TODO
        on_error.delay(batch_id)
        return

    if job['status'] == 'Running':
        new_status = models.Batch.Status.RUNNING.value
    elif job['status'] == 'Starting':
        new_status = models.Batch.Status.STARTING.value
    elif job['status'] == 'Scheduling':
        new_status = models.Batch.Status.SCHEDULING.value
    elif job['status'] == 'Succeed':
        new_status = success_status
        if not all_dags_successed:
            on_error.delay(
                batch_id, models.Batch.FailureKind.SYSTEM,
                "job has ran successfully but there are stil some dags not",
            )
            return
    else:
        new_status = batch.status

    if eva.domain == Evaluation.Domain.NLP:
        # HuggingFace 模型评测失败后自动重试 3 次。
        if new_status == models.Batch.Status.FAILURE and "/" in eva.name and batch.try_sequence < 3:
            from .views import BatchResumption
            BatchResumption.resume_failed_batch(eva, batch)
            # Avoid updating batch status to FAILURE.
            return

    if batch.status != new_status:
        batch.status = new_status
        batch.save()
        notify_status.delay(batch_id)
    else:
        batch.save()

    if job['status'] != 'Succeed':
        watch_batch.apply_async(
            args=(batch_id, ),
            countdown=30,
        )


def _handle_joint_dags(batch: models.Batch, try_sequence: int, dags_status: List[Dict[str, Any]]) -> bool:
    batch_id = batch.pk
    queryset = models.DAG.objects.defer("result").filter(
        batch_id=batch_id,
        deleted_at=None,
    )
    dags = {x.dag_id: x for x in queryset}
    datasets: Dict[int, Dataset] = {x.pk: x for x in Dataset.objects.all()}

    for item in dags_status:
        dag = dags[item['id']]
        new_status = item['status']
        if dag.status == new_status:
            continue

        dag.status = new_status

        if new_status != models.Batch.Status.SUCCESS.value:
            dag.save()
            continue

        if not datasets[dag.dataset_id].is_objective:
            dag.status = models.Batch.Status.DONE_INFERENCE

        result = executor.service.load_batch_dag_result(batch_id, try_sequence, dag.dag_id)
        if result is None:
            continue

        _save_dag_result(batch_id, try_sequence, dag, result)

        dag.save()

    for dag in dags.values():
        if dag.status not in models.Batch.SUCCESS_STATUSES:
            return False  # not all dags successed
    return True


def _save_dag_result(batch_id: int, try_sequence: int, dag: models.DAG, result: Dict[str, Any]):
    dag.result = result['raw']
    metrics: Dict[str, Any] = result['metric']
    if metrics:
        dag.started_at = metrics['started_at']
        dag.stopped_at = metrics['stopped_at']
        dag.metrics = metrics['metrics']
    if not _is_dataset_success(dag):
        return

    ds_ret = executor.service.load_batch_dataset_result(
        batch_id,
        try_sequence,
        dag.dataset_id,
        dag.disturbance,
    )
    if ds_ret is None:
        return

    defaults = dict(
        scenario_entry_point=dag.scenario_entry_point,
        result=ds_ret['result'],
        updated_at=timezone.now(),
    )
    if 'started_at' in ds_ret:
        defaults.update(
            started_at=ds_ret['started_at'],
            stopped_at=ds_ret['stopped_at'],
            total_instances=ds_ret['total'],
            avg_elapsed=ds_ret['avg'],
            max_elapsed=ds_ret['max'],
        )
    create_defaults = dict(
        created_at=timezone.now(),
    )
    create_defaults.update(defaults)
    # Task summarize
    filters = dict(
        batch_id=dag.batch_id,
        dataset_id=dag.dataset_id,
        disturbance=dag.disturbance,
    )
    dt_ret = models.DatasetResult.objects.filter(**filters).first()
    if dt_ret is None:
        models.DatasetResult.objects.create(**filters, **create_defaults)
    else:
        for k, v in defaults.items():
            setattr(dt_ret, k, v)
        dt_ret.save()


def _is_dataset_success(current_success_dag: models.DAG) -> bool:
    return models.DAG.objects.defer("result").filter(
        ~Q(status__in=models.Batch.SUCCESS_STATUSES),
        ~Q(pk=current_success_dag.pk),
        disturbance=current_success_dag.disturbance,
        batch_id=current_success_dag.batch_id,
        scenario_entry_point=current_success_dag.scenario_entry_point,
        dataset_id=current_success_dag.dataset_id,
        deleted_at=None,
    ).count() == 0


def _prepare_dags(batch: models.Batch, try_sequence: int) -> bool:
    dags_ready = True
    for package, item in batch.dags_delayed_tasks.items():
        if item['dags_ready']:
            continue
        loaded_dags = executor.service.load_batch_delayed_dags(batch.pk, package, try_sequence)
        if loaded_dags is None:
            dags_ready = False
            continue
        batch.dags_delayed_tasks[package]['dags_ready'] = True
        with transaction.atomic():
            for dag in loaded_dags:
                models.DAG.objects.create(
                    evaluation_id=dag['evaluation_id'],
                    batch_id=dag['batch_id'],
                    scenario_entry_point=dag['scenario_entry_point'],
                    dataset_id=dag['dataset_id'],
                    delayed_uuid=dag['delayed_uuid'],
                    run_entry=dag['run_entry'],
                    result=dag['result'],
                    status=models.Batch.Status.PENDING,
                    created_at=timezone.now(),
                )

    batch.dags_ready = dags_ready
    batch.save()
    return dags_ready


def save_batch_results(batch: models.Batch) -> List[Dict[str, Any]]:
    batch_results = executor.service.load_batch_result(batch.pk, batch.try_sequence)
    if batch_results is None:
        return []
    try:
        ds = models.DatasetResult.objects.get(batch_id=batch.pk, dataset_id=0, disturbance='')
        ds.result = batch_results
        ds.updated_at = timezone.now()
        ds.save()
    except models.DatasetResult.DoesNotExist:
        models.DatasetResult.objects.create(
            batch_id=batch.pk,
            dataset_id=0,
            disturbance='',
            result=batch_results,
            created_at=timezone.now(),
        )
    batch.results = list(batch_results.values())
    return batch.results


@shared_task
def notify_status(batch_id: int, marking=False):
    return
    from ..user.util import send_task_status
    from ..user.models import User

    batch = models.Batch.objects.get(pk=batch_id)

    if batch.dry_run or batch.user_id == 0:
        return

    notification_key = f'batch-status-notification-{batch.pk}-{batch.status}'
    if cache.get(notification_key) is not None:
        logger.warning(
            f"Duplicated email notification, batch={batch.pk}, status={batch.status},"
            f"evaluation_id={batch.evaluation_id}"
        )
        return

    cache.set(notification_key, 1, 3600 * 24 * 7)

    eva = Evaluation.objects.get(pk=batch.evaluation_id)
    user = User.objects.get(pk=eva.user_id)

    status_text_map = {
        models.Batch.Status.PENDING.value: '已进入排队中',
        models.Batch.Status.PREPARING.value: '准备提交算力平台',
        models.Batch.Status.ENQUEUED.value: '已提交算力平台',
        models.Batch.Status.STARTING.value: '已进入启动中',
        models.Batch.Status.SCHEDULING.value: '已进入调度中',
        models.Batch.Status.RUNNING.value: '已进入运行中',
        models.Batch.Status.SUCCESS.value: '运行成功',
        models.Batch.Status.FAILURE.value: '运行失败',
        models.Batch.Status.CANCEL.value: '已停止',
        models.Batch.Status.DONE_INFERENCE: '推理完成',
    }
    subject: str = '任务状态通知'
    if marking:
        status_text_map[models.Batch.Status.SUCCESS] = '主观推理评测已经完成'
        subject = '主观推理任务评测结果通知'
    if batch.status in [
            models.Batch.Status.MODIFIED,
            models.Batch.Status.PREPARING.value,
            models.Batch.Status.ENQUEUED,
    ]:
        return

    if user.sa_email is not None:
        logger.info(
            "sending status email, batch_id=%s, eval_id=%s, status=%s, email=%s",
            batch_id, batch.evaluation_id, batch.status, user.sa_email,
        )

        send_task_status(
            to=user.sa_email,
            eval_id=batch.evaluation_id,
            model_name=eva.name,
            llm_parameters=eva.llm_parameters,
            batch_version=batch.sequence,
            status_text=status_text_map[batch.status],
            subject=subject,
        )
    else:
        logger.warn(
            f"no status email was sent, batch_id={batch_id}, "
            f"eval_id={batch.evaluation_id},"
            f"status={batch.status}"
        )


_chat_completions_suffix = '/chat/completions'

def _trim_chat_completions(remote_url: str) -> str:
    if remote_url.endswith(_chat_completions_suffix):
        return remote_url[:-len(_chat_completions_suffix)]
    return remote_url
