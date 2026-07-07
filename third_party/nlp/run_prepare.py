#!/usr/bin/env python
import collections
import json
import os
import uuid
from typing import List, Dict, Any

from feam import load_nlp_scenario, Options
from feam.nlp import NLPBaseScenario
from feam.models import Scenario

from run_lib import write_result, get_server_url


def main(package: str):
    with open('dags-delayed-tasks.json') as f:
        content = json.load(f)

    package_detail = content.get(package)
    if not package_detail:
        return
    delayed_tasks = package_detail['tasks']
    by_task_ids: Dict[str, Dict[str, Any]] = {}
    for tasks in delayed_tasks.values():
        for item in tasks:
            by_task_ids[item['feam_task_id']] = item

    dags: List[Dict[str, Any]] = []
    contexts_by_task: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for entrypoint in delayed_tasks.keys():
        scenario = load_scenario(entrypoint, package_detail['options'])
        for task in scenario.create_tasks():
            if task.id() not in by_task_ids:
                print(f'DBG: Ignore {entrypoint}.{task.id()} as it\'s not in the list {by_task_ids}')
                continue
            item = by_task_ids[task.id()]
            for ds in task.create_datasets():
                dag_id = str(uuid.uuid4())
                dags.append(dict(
                    evaluation_id=item['evaluation_id'],
                    batch_id=item['batch_id'],
                    delayed_uuid=dag_id,
                    scenario_entry_point=entrypoint,
                    dataset_id=item['dataset_id'],
                    run_entry=ds.id(),
                    result={},
                ))
                contexts_by_task[item['feam_task_id']].append(dict(
                    batch_id=item['batch_id'],
                    evaluation_id=item['evaluation_id'],
                    dataset_id= item['dataset_id'],
                    dag_id=dag_id,
                    disturbance='',
                    pending=True,
                    run_unit=dict(
                        scenario_entry_point=entrypoint,
                        task_id=item['feam_task_id'],
                        dataset_id=ds.id(),
                    ),

                ))

    batch_id = os.environ['RUNNING_BATCH_ID']
    write_result(f'batch-{batch_id}-package-{package}-delayed-dags.json', dags)

    all_contexts: List[Dict[str, Any]] = []
    for task_id, contexts in contexts_by_task.items():
        # TODO subjective
        with open(f'{package}-{task_id}-contexts.json', 'w') as f:
            json.dump(contexts, f)
        all_contexts.extend(contexts)

    with open(f'{package}-all-ctxs.json', 'w') as f:
        json.dump(all_contexts, f)


def load_scenario(entry_point: str, options: Dict[str, Any]) -> Scenario:
    server_url = options['server_url'] or get_server_url(1)
    model_name = NLPBaseScenario.get_model_name(server_url)  or options['model']
    return load_nlp_scenario(
        entry_point, Options(
            server_url=server_url,
            model=model_name,
            extras=options['extras'],
        ),
    )



if __name__ == '__main__':
    import sys

    main(sys.argv[1])
