import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

from filelock import FileLock


STATUS_PENDING = 'P'
STATUS_RUNNING = 'R'
STATUS_SUCCESS = 'S'
STATUS_FAILURE = 'F'


DISTURBNACE_METHOD_DATASET = 'D'
DISTURBANCE_MEtHOD_REFERENCE_PREFIX = 'RefPre'

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
    disturbance: str
    disturbance_opts: dict
    run_unit: RunUnit
    pending: bool = True

    @property
    def reference_prefix(self) -> Optional[str]:
        return self.disturbance_opts.get('reference_prefix') or None


def read_all_contexts(context_json: str) -> List[DAGContext]:
    thirdparty_path = os.environ['THIRD_PARTY']
    with open(os.path.join(thirdparty_path, context_json)) as f:
        raw_ctxs = json.load(f)
        print('<-', '-' * 20, 'Begin of Contexts', '-' * 20, '->')
        print(json.dumps(raw_ctxs, indent=2))
        print('<-', '-' * 20, 'End of Contexts', '-' * 20, '->')
        return [
            DAGContext(
                evaluation_id=x['evaluation_id'],
                batch_id=x['batch_id'],
                dataset_id=x['dataset_id'],
                dag_id=x['dag_id'],
                disturbance=x.get('disturbance') or '',
                disturbance_opts=x.get('disturbance_opts') or {},
                pending=x['pending'],
                run_unit=RunUnit(
                    scenario_entry_point=x['run_unit']['scenario_entry_point'],
                    task_id=x['run_unit']['task_id'],
                    dataset_id=x['run_unit']['dataset_id'],
                ),
            )
            for x in raw_ctxs
        ]


def get_datasets_results(contexts: List[DAGContext]) -> List[Tuple[DAGContext, Any]]:
    by_names: Dict[str, DAGContext] = {}
    for ctx in contexts:
        by_names[_get_dataset_result_name(ctx)] = ctx
    results = []
    for name, ctx in by_names.items():
        try:
            results.append((ctx, get_result(name)))
        except FileNotFoundError:
            pass

    return results


def write_dataset_result(ctx: DAGContext, results: Any):
    write_result(_get_dataset_result_name(ctx), results)


def _get_dataset_result_name(ctx: DAGContext) -> str:
    return f'batch-{ctx.batch_id}-dataset-{ctx.dataset_id}-disturbance-{ctx.disturbance}.json'


def write_dag_result(ctx: DAGContext, results: Any):
    write_result(_get_dag_result_name(ctx), results)


def get_dag_result(ctx: DAGContext) -> Any:
    return get_result(_get_dag_result_name(ctx))


def _get_dag_result_name(ctx: DAGContext) -> str:
    return f'batch-{ctx.batch_id}-dag-{ctx.dag_id}.json'


def write_batch_result(ctx: DAGContext, r, verbose=False):
    write_result(_get_batch_result_name(ctx), r, verbose)


def get_batch_result(ctx: DAGContext) -> Dict[str, Any]:
    try:
        return get_result(_get_batch_result_name(ctx))
    except FileNotFoundError:
        return {}


def _get_batch_result_name(ctx: DAGContext) -> str:
    return f'batch-{ctx.batch_id}-result.json'


def init_status(ctxs: List[DAGContext]):
    for ctx in ctxs:
        do_set_status(ctx, STATUS_PENDING)


def set_status(ctx: DAGContext, status: str, **kwargs):
    lock = FileLock(f"batch-status-{ctx.batch_id}.lock")
    with lock:
        do_set_status(
            ctx,
            status,
            **kwargs,
        )


def _get_status_name(ctx: DAGContext) -> str:
    return f'batch-{ctx.batch_id}-status.json'


def do_set_status(ctx: DAGContext, status: str, **kwargs):
    name = _get_status_name(ctx)
    dest = get_path(name)
    if os.path.exists(dest):
        with open(dest, 'r') as f:
            r = json.load(f)
    else:
        r: Dict[str, Any] = {}

    if 'dags' not in r:
        r['dags'] = []

    dags: List[Dict[str, Any]] = r['dags']

    found = False
    for item in dags:
        if item['id'] == ctx.dag_id:
            item['status'] = status
            item.update(kwargs)
            found = True

    if not found:
        item = {'id': ctx.dag_id, 'status': status}
        item.update(kwargs)
        dags.append(item)

    all_successed = all(x['status'] in [STATUS_SUCCESS] for x in r['dags'])

    if all_successed:
        r['status'] = STATUS_SUCCESS
    elif status != STATUS_SUCCESS:
        r['status'] = status
    write_result(name, r)


def is_all_dags_successed(ctx: DAGContext) -> bool:
    with open(get_path(_get_status_name(ctx))) as f:
        r = json.load(f)

    return r['status'] == STATUS_SUCCESS


def get_result(name: str):
    filepath = get_path(name)
    _, filename = os.path.split(filepath)
    if os.path.exists(filename):
        print(
            f"Found result exists in current directory, "
            f"read {filename} instead of {filepath}",
        )
        filepath = filename

    with open(filepath) as f:
        return json.load(f)


def write_result(name: str, results: Any, verbose=False):
    result_path = get_path(name)
    f = tempfile.NamedTemporaryFile('w', delete=False)
    json.dump(results, f)
    f.close()
    if verbose:
        with open(f.name, 'r') as fp:
            print(f'Wrote result into temporary file {f.name}...')
            print(f'--- BEGIN OF CONTENT --- ')
            print(fp.read())
            print('--- END OF CONTENT ---')
    os.chmod(f.name, 0o644)
    shutil.move(f.name, result_path)
    if verbose:
        print(f'Moved temporary file {f.name} to {result_path}.')


def get_path(name: str) -> str:
    prefix = os.environ['OUTPUT_PREFIX']
    return os.path.join(os.environ['OUTPUT_DIR'], f'{prefix}{name}')


def get_server_url(workers) -> str:
    url = f"http://127.0.0.1:15001/func?workers={int(workers)}"
    if os.environ.get('REMOTE_API'):
        url = os.environ['REMOTE_API']
    return url
