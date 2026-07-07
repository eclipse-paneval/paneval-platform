#!/usr/bin/env python
import contextlib
import json
import multiprocessing
import os
import signal
import sys
import time
import argparse
from collections import defaultdict
from multiprocessing.managers import SyncManager
from typing import Optional, Dict, Any, List, Tuple

from feam import load_nlp_scenario, Options
from feam.nlp import NLPBaseScenario
from feam.models import DatasetMetric, TaskMetric, Scenario, Metric
from feam.runner import DatasetStateRunner

from run_lib import set_status, init_status
from run_lib import get_server_url, write_dataset_result
from run_lib import write_dag_result, write_batch_result, get_batch_result, get_dag_result
from run_lib import STATUS_FAILURE, STATUS_RUNNING, STATUS_SUCCESS
from run_lib import DAGContext, read_all_contexts
from run_lib import DISTURBNACE_METHOD_DATASET


class TaskRunner:
    def __init__(self, num_workers: int, data_workers: int, manager: SyncManager):
        self.num_workers = max(num_workers, 1)
        self.data_workers = max(data_workers, 1)
        self.manager = manager
        self._process: List[multiprocessing.Process] = []
        self.queue = manager.Queue(maxsize=self.num_workers * 102400)
        self.scenarios: Dict[str, Scenario] = {}

    def start(self):
        if self.num_workers <= 1:
            return

        for _ in range(self.num_workers):
            p = multiprocessing.Process(target=self._run, args=(self.queue,))
            self._process.append(p)
            p.start()

    def _run(self, queue: multiprocessing.Queue):
        while True:
            job = queue.get()
            if job is None:
                break

            try:
                self._run_job(job)
            except:
                import traceback

                print("Uncaught exception cause suicide...", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                parent_pid = os.getppid()
                print("Sending %d to %d..." % (signal.SIGTERM, parent_pid), file=sys.stderr)
                os.kill(parent_pid, signal.SIGTERM)
                raise

    def _run_job(self, job: Tuple[str, str, List[DAGContext], bool]):
        entry_point, task_id, ctxs, dry_run = job
        if entry_point not in self.scenarios:
            self.scenarios[entry_point] = load_scenario(
                entry_point,
                dry_run,
                reference_prefix=ctxs[0].reference_prefix,
                workers=self.data_workers,
            )
        self._do_run_job(self.scenarios[entry_point], task_id, ctxs, dry_run)

    def _do_run_job(
            self,
            scenario: Scenario,
            task_id: str,
            ctxs: List[DAGContext],
            dry_run: bool,
    ):
        ctx = ctxs[0]
        ret, result = run_task(
            scenario, task_id, ctxs,
            dry_run=dry_run,
        )

        r: Dict[str, Any] = dict(
            batch_id=ctx.batch_id,
            scenario_entry_point=ctx.run_unit.scenario_entry_point,
            dataset_id=ctx.dataset_id,
        )
        if ret is not None:
            metric = ret.metric
            r.update(
                result=ret.raw,
            )
            if metric is not None:
                r.update(
                    started_at=metric.started_at,
                    stopped_at=metric.stopped_at,
                    total=metric.total,
                    avg=metric.avg,
                    max=metric.max,
                )
        else:
            r.update(
                result=result,
            )

        write_dataset_result(ctx, r)

    def wait(self, timeout) -> bool:
        if self.num_workers <= 1:
            return True

        for _ in range(self.num_workers):
            self.queue.put(None)

        all_terminated = True
        for t in self._process:
            t.join(timeout=timeout)
            if t.is_alive():
                all_terminated = False

        return all_terminated

    def enqueue(
            self,
            scenario_entry_point: str,
            task_id: str,
            ctxs: List[DAGContext],
            dry_run: bool,
    ):
        job = (scenario_entry_point, task_id, ctxs, dry_run)
        if self.num_workers <= 1:
            self._run_job(job)
        else:
            self.queue.put(job)


def run(package: str, context_json: str, dry_run: bool, runner: TaskRunner) -> List[DAGContext]:
    contexts: List[DAGContext] = read_all_contexts(context_json)
    # Only run pending dags
    contexts: List[DAGContext] = [x for x in contexts if x.pending]
    init_status(contexts)
    scenarios_by_disturbance: Dict[str, List[DAGContext]] = defaultdict(list)
    for ctx in contexts:
        scenarios_by_disturbance[ctx.disturbance].append(ctx)
    for dis, ctxs in scenarios_by_disturbance.items():
        print('<-', '-' * 20, f'Begin of Disturbance: {dis}', '-' * 20, '->')
        ctx = ctxs[0]
        groupby_scenarios: Dict[str, List[DAGContext]] = defaultdict(list)
        for ctx in ctxs:
            groupby_scenarios[ctx.run_unit.scenario_entry_point].append(ctx)

        for entry_point, ctxs in groupby_scenarios.items():
            run_scenario(entry_point, ctxs, dry_run, runner)

        print('<-', '-' * 20, f'End of Disturbance: {dis}', '-' * 20, '->')

    # Harness
    if os.path.exists(f'{package}-all-ctxs.json'):
        return read_all_contexts(f'{package}-all-ctxs.json')
    return contexts


def run_scenario(
        entry_point: str,
        contexts: List[DAGContext],
        dry_run: bool,
        runner: TaskRunner,
):

    groupby_tasks: Dict[str, List[DAGContext]] = defaultdict(list)
    for ctx in contexts:
        groupby_tasks[ctx.run_unit.task_id].append(ctx)

    for task_id, ctxs in groupby_tasks.items():
        runner.enqueue(entry_point, task_id, ctxs, dry_run)


def load_scenario(entry_point: str, dry_run: bool = False, reference_prefix: Optional[str] = None, workers: int = 1) -> Scenario:
    thirdparty_path = os.environ['THIRD_PARTY']
    tokenizer_path = os.path.join(thirdparty_path, "tokenizer.json")
    tokenizer: Optional[Dict[str, Any]] = None
    if os.path.exists(tokenizer_path):
        with open(tokenizer_path) as f:
            tokenizer = json.load(f)
            custom_tokenizer = os.path.join(thirdparty_path, 'tokenizer')
            if os.path.isdir(custom_tokenizer):
                tokenizer['tokenizer_name'] = custom_tokenizer  # type: ignore
    url = get_server_url(workers)
    model_name = NLPBaseScenario.get_model_name(url)  # type: ignore
    batch_id: int = int(os.environ['RUNNING_BATCH_ID'])
    write_model_name(batch_id, model_name or '')

    options = Options(
        server_url=url,
        model=model_name or "BAAI/chat-glm-130b",
        extras={
            "max_eval_instances": 1 if dry_run else 1000,
            "tokenizer": tokenizer,
            "dry_run": dry_run,
            'reference_prefix': reference_prefix,
        },
    )

    return load_nlp_scenario(entry_point=entry_point, options=options)


def link_absent_files(src: str, dst: str):
    def get_dstpath(dirname: str, item: str) -> str:
        fullpath = os.path.join(dirname, item)
        relpath = os.path.relpath(fullpath, src)
        dstpath = os.path.join(dst, relpath)
        return dstpath

    # print('<-', '-' * 20, f'Begin link absent files from {src} to {dst}')
    for (dirname, dirs, files) in os.walk(src):
        for item in dirs:
            dstpath = get_dstpath(dirname, item)
            if not os.path.exists(dstpath):
                os.mkdir(dstpath)

        for item in files:
            fullpath = os.path.join(dirname, item)
            dstpath = get_dstpath(dirname, item)

            if os.path.islink(dstpath):
                os.unlink(dstpath)

            if not os.path.exists(dstpath):
                try:
                    os.symlink(fullpath, dstpath)
                except FileExistsError:
                    pass
    # print('<-', '-' * 20, f'End link absent files from {src} to {dst}')


def run_task(
        scenario: Scenario,
        task_id: str,
        ctxs: List[DAGContext],
        dry_run: bool,
) -> Tuple[Optional[TaskMetric], List[Dict[str, Any]]]:
    metrics: List[DatasetMetric] = []
    dag_results: List[Dict[str, Any]] = []
    for ctx in ctxs:
        set_status(ctx, STATUS_RUNNING)
        try:
            result, metric = run_dag(scenario, ctx, dry_run=dry_run)
        except Exception as e:
            set_status(ctx, STATUS_FAILURE, failure_details=str(e.args[0]))
            raise
        if dry_run:
            result['disturbance'] = ctx.disturbance
        dag_results.append(result)
        if not _require_holding():
            set_status(ctx, STATUS_SUCCESS)
        write_dag_result(ctx, {'raw': result, 'metric': metric})
        if not dry_run:
            metrics.append(DatasetMetric(
                raw=result,
                started_at=metric['started_at'],
                stopped_at=metric['stopped_at'],
                metrics=metric['metrics'],
            ))

    if not dry_run:
        task = scenario.lookup_task(task_id)
        if task is None:
            raise RuntimeError(f"couldn't find task {task_id}")
        return task.summarize(metrics), dag_results
    return None, dag_results


def _require_holding():
    return os.environ.get('HOLD_PENDING_FOR_JUDGE') == '1'


def run_dag(
        scenario: Scenario,
        ctx: DAGContext,
        dry_run: bool,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    runner = DatasetStateRunner(
        scenario, ctx.run_unit.task_id, ctx.run_unit.dataset_id,
        dry_run=dry_run,
    )
    gen = runner.run()
    while True:
        try:
            next(gen)
        except StopIteration as e:
            return e.value


def write_model_name(batch_id: int, val: str):
    prefix = os.environ['OUTPUT_PREFIX']
    path = os.path.join(os.environ['OUTPUT_DIR'], f'{prefix}{batch_id}-model')
    with open(path, 'w') as f:
        f.write(val)


def summarize(contexts: List[DAGContext], dry_run: bool, verbose=False, workers=1):
    from run_lib import get_datasets_results

    by_disturbances: Dict[str, List[Tuple[DAGContext, Any]]] = defaultdict(list)
    disturbance_to_ref_prefixes: Dict[str, Optional[str]] = {}

    for ctx, result in get_datasets_results(contexts):
        by_disturbances[ctx.disturbance].append((ctx, result))
        disturbance_to_ref_prefixes[ctx.disturbance] = ctx.reference_prefix

    task_id_to_ctxs: Dict[str, DAGContext] = {x.run_unit.task_id: x for x in contexts}

    results: List[Dict[str, Any]] = []
    for disturbance, ds_results in sorted(by_disturbances.items(), key=lambda x: x[0]):
        results.extend(_do_summarize(
            disturbance, ds_results, dry_run, task_id_to_ctxs,
            reference_prefix=disturbance_to_ref_prefixes[disturbance],
            workers=workers,
        ))

    existed_results: Dict[str, Any] = get_batch_result(contexts[0])
    for item in results:
        key = f'{item["dataset_key"]}-{item["disturbance"]}'
        existed_results[key] = item

    write_batch_result(contexts[0], existed_results, verbose)


def _do_summarize(
        disturbance: str,
        dataset_results: List[Tuple[DAGContext, Any]],
        dry_run: bool,
        task_id_to_ctxs: Dict[str, DAGContext],
        reference_prefix: Optional[str] = None,
        workers: int = 1,
) -> List[Dict[str, Any]]:
    by_scenarios: Dict[str, List[TaskMetric]] = defaultdict(list)

    for ctx, item in dataset_results:
        metric: Optional[Metric] = None
        if item.get('started_at') is not None:
            metric = Metric(
                started_at=item['started_at'],
                stopped_at=item['stopped_at'],
                total=item['total'],
                avg=item['avg'],
                max=item['max'],
            )

        by_scenarios[ctx.run_unit.scenario_entry_point].append(TaskMetric(
            raw=item['result'],
            metric=metric,
        ))


    results: List[Dict[str, Any]] = []
    for entry_point, metrics in by_scenarios.items():
        scenario = load_scenario(entry_point, reference_prefix=reference_prefix, workers = workers)
        if dry_run:
            results.append({
                'dataset_key': entry_point,
                'disturbance': disturbance,
                'details': [y for x in metrics for y in x.raw]
            })
            continue

        stat = scenario.summarize(metrics)

        # 更新细则中的数据集 ID 用于前端关联
        for item in stat.details:
            item['dataset_id'] = task_id_to_ctxs[item['key']].dataset_id

        results.append({
            'disturbance': disturbance,
            'dataset_key': entry_point,
            'accuracy': stat.accuracy,
            'calibration': stat.calibration,
            'robustness': stat.robustness,
            'fairness': stat.fairness,
            'bias': stat.bias,
            'win_rate': stat.win_rate,
            "details": stat.details,
        })
    return results


if __name__ == '__main__':
    args = sys.argv

    parser = argparse.ArgumentParser(
        prog='run_feam.py',
        description='An run_feam.py description',
        epilog='Copyright(r), 2024',
    )

    parser.add_argument('-p', '--package', required=True)
    parser.add_argument('-c', '--context', required=True)
    parser.add_argument('-d', '--dry_run', required=True)
    parser.add_argument('-n', '--num_workers',  required=False)
    parser.add_argument('-w', '--data_workers', required=False)

    args = parser.parse_args()

    package = args.package
    context_json = args.context
    dry_run = args.dry_run
    num_workers, data_workers = 1,1
    if args.num_workers is not None:
        num_workers = int(args.num_workers)
    if args.data_workers is not None:
        data_workers = int(args.data_workers)
    #if len(sys.argv) == 6:
    #    package, context_json, dry_run, num_workers, data_workers = sys.argv[1:]
    #    num_workers = int(num_workers)
    #    data_workers = int(data_workers)
    #else:
    #    package, context_json, dry_run = sys.argv[1:]

    dry_run = dry_run == '1'
    with multiprocessing.Manager() as manager:
        runner = TaskRunner(num_workers, data_workers, manager)
        runner.start()
        contexts = []
        try:
            contexts = run(package, context_json, dry_run, runner)
        finally:
            print("All tasks were enqueued, now wait them to be done.")
            while True:
                all_terminated = runner.wait(15)
                if all_terminated:
                    break
                print("Tasks are still running")
                summarize(contexts, dry_run, workers=data_workers)
        time.sleep(10)
        print("Tasks are completed.")
        summarize(contexts, dry_run, verbose=True, workers=data_workers)
