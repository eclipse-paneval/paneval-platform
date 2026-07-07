import csv
import json
import sys
import subprocess
import os
import tempfile
from dataclasses import replace
from typing import List

from feam.models import Task, Dataset, RequestState, DatasetMetric, TaskMetric, Meta

_ENV_COPY_KEYS = [
    'EVALUATION_MODEL_NAME',
    'REMOTE_API',
    'EVALUATION_GEN_KWARGS',
    'EVALUATION_BATCH_SIZE',
    'EVALUATION_NUM_RETRY',
    'EVALUATION_MODEL_TOKENIZER',
]


class OpenCompassTask(Task):
    def __init__(
            self,
            meta: Meta,
            model,
            tasks,
    ):
        self.tasks = tasks
        self._output_path = tempfile.mkdtemp()
        cur_dir = os.path.abspath(os.path.dirname(__file__))
        self.conf_tmpl = os.path.join(cur_dir, 'eval.py.tmpl')
        self.conf = os.path.join(cur_dir, 'eval.py')
        self._args = [
            '-w', self._output_path,
            self.conf,
        ]
        self.meta = meta

    def create_datasets(self) -> List[Dataset]:
        return [DummyDataset(self.meta.name)]

    def execute(self, instance: RequestState) -> RequestState:
        instance.record_init_at()
        instance.record_request_at()
        with open(self.conf_tmpl, 'r') as f:
            tmpl = f.read()

        if self.meta.server_url.startswith("http"):
            base_url = self.meta.server_url
            suffix = '/chat/completions'
            if base_url.endswith(suffix):
                base_url = base_url[:-len(suffix)]
            os.environ['OPENAI_BASE_URL'] = base_url
            os.environ.setdefault("OPENAI_API_KEY", "dummy")
            print(f'env OPENAI_BASE_URL={os.environ["OPENAI_BASE_URL"]}')
            print(f'env OPENAI_API_KEY={os.environ["OPENAI_API_KEY"]}')

        with open(self.conf, 'w') as f:
            f.write('environ = {}\n')
            env = {}
            env['OPENCOMPASS_TASK'] = self.tasks

            for k, v in os.environ.items():
                if k in _ENV_COPY_KEYS:
                    env[k] = v
            for k, v in env.items():
                f.write(f'environ["{k}"] = "{v}"\n')
            f.write(tmpl)
        cmd = [sys.executable, "-m", "opencompass.cli.main"] + self._args
        print(cmd)
        subprocess.check_call(cmd)
        instance.record_response_at()
        raw = []
        for (dirname, _, files) in os.walk(self._output_path):
            for item in files:
                csv_file = os.path.join(dirname, item)
                print(f"Finding CSV files in output directory, got {csv_file}")
                if csv_file.endswith(".csv"):
                    with open(csv_file) as f:
                        reader = csv.reader(f, delimiter=',')
                        header = []
                        rows = []
                        for i, row in enumerate(reader):
                            if i == 0:
                                header = row
                            else:
                                d = dict(zip(header, row))
                                rows.append(d)
                        raw.append(rows)
        return replace(instance, raw={'states': raw})

    def summarize(self, stats: List[DatasetMetric]) -> TaskMetric:
        raw = {
            'key': self.id(),
            'results': [
                s
                for x in stats
                for y in x.raw['states']
                for s in y['states']
            ],
            'accuracy': 0,
        }
        return TaskMetric(
            raw,
            metric=TaskMetric.get_timeline_metrics(stats),
        )

    def get_meta(self) -> Meta:
        return self.meta


class DummyDataset(Dataset):
    def __init__(self, name: str):
        self.name = name

    def create_instances(self) -> List[RequestState]:
        return [
            RequestState(
                raw={}
            )
        ]

    def summarize(self, states: List[RequestState]) -> DatasetMetric:
        started_at, stopped_at, elapseds = DatasetMetric.get_timeline_metrics(states)
        return DatasetMetric(
            raw={
                'states': [x.raw for x in states],
            },

            started_at=started_at,
            stopped_at=stopped_at,
            metrics={
                'elapseds': elapseds,
            },
        )

    def id(self) -> str:
        return f'builtin.lmeval.qa.en:{self.name}'


def get_gpu_devices() -> str:
    output = subprocess.check_output(["nvidia-smi", "-L"])
    gpus = []
    for line in output.splitlines():
        gpus.append(
            line.split()[1].decode('utf-8')[:-1] # Remove trail :
        )
    return ','.join(gpus)
