import json
import sys
import subprocess
import os
import tempfile
from dataclasses import replace
from typing import List

from feam.models import Task, Dataset, RequestState, DatasetMetric, TaskMetric, Meta
from lm_eval import tasks as _p_tasks


class LMEvalTask(Task):
    def __init__(
            self,
            meta: Meta,
            model,
            tasks,
            num_fewshot=0,
            batch_size='auto',
    ):
        if 'CUDA_VISIBLE_DEVICES' in os.environ:
            devices = os.environ['CUDA_VISIBLE_DEVICES']
        else:
            devices = get_gpu_devices()
        self._output_path = tempfile.mkdtemp()
        self.gpu_ids = [x.strip() for x in devices.split(',') if x.strip()]
        dt_path = os.environ.get('LMEVAL_DATASET_DOWNLOAD_PATH', '/share/project/qbw/lm_eval')
        self.dry_run = int(os.environ.get('DRY_RUN_BATCH', 0)) == 1
        print("dry_run", self.dry_run, type(self.dry_run))
        new_s8_json_path = os.path.join(dt_path, 's8/s8.json')
        s8_templ_path = os.path.join(dt_path, 's8/_template_yaml.yaml')
        replace_cmd = f"sed -i -e 's;/home/qinbowen/lm-evaluation-harness-flageval/lm_eval/tasks/s8/s8.json;{new_s8_json_path};' {s8_templ_path}"
        print('+', replace_cmd)
        os.system(replace_cmd)
        tasks_dir = os.path.dirname(_p_tasks.__file__)
        link_cmd = f'ln -sf {os.path.join(dt_path, "livebench")} {tasks_dir}/livebench'
        link_cmd += f'&& ln -sf {os.path.join(dt_path, "musr_generative")} {tasks_dir}/musr_generative'
        print('+', link_cmd)
        os.system(link_cmd)
        self._args = [
            '--tasks', tasks,
            '--output_path', self._output_path,
            '--batch_size', os.environ.get('EVALUATION_BATCH_SIZE','1'),
            '--include_path', os.environ.get('LMEVAL_DATASET_DOWNLOAD_PATH', '/share/project/qbw/lm_eval'),
        ]
        #'--num_fewshot', str(num_fewshot),

        model_type = os.environ.get('EVALUATION_MODEL_TYPE')
        if model_type and model_type.lower() == "chat":
            self._args.append('--apply_chat_template')

        self.meta = meta
        self.special_model_name = model
        hugginface_prefix = 'hf://'
        openai_prefixes = ['http://', 'https://']
        model_args = []
        localtasks = [
                       "mmlu",
                       "cmmlu",
                       "gsm8k",
                       "leaderboard_bbh",
                       "hellaswag",
                       "truthfulqa_mc1",
                       "winogrande",
                       "commonsense_qa",
                       "piqa",
                       "openbookqa",
                       "boolq",
                       "arc_easy",
                       "arc_challenge",
                       "minerva_math_algebra",
                       "ceval-valid"
                ]
        if meta.server_url.startswith(hugginface_prefix):
            model_url = meta.server_url[len(hugginface_prefix):]
            self._args.extend(['--model', 'hf'])

            model_args = [
                f'pretrained={model_url}'
            ]

            if len(self.gpu_ids) > 1:
                model_args.append('parallelize=True')

            model_args.append('trust_remote_code=True')
            cache_path = os.environ.get('EVALUATION_CACHE_PATH')
            if cache_path and not self.dry_run:
                cachepath = os.path.join(cache_path, tasks)
                self._args.extend([
                    '--use_cache', cachepath
                ])
        elif any(meta.server_url.startswith(x) for x in openai_prefixes):
            if tasks in localtasks:
                self._args.extend([
                    '--model', 'local-completions',
                ])
                meta.server_url = meta.server_url.replace('/chat','')
                model_args.append('trust_remote_code=True')
            else:
                self._args.extend([
                    '--model', 'openai-chat-completions',
                    '--apply_chat_template'
                ])
            model_name = os.environ['EVALUATION_MODEL_NAME']
            num_concurrent = os.environ.get('EVALUATION_NUM_CONCURRENT', '1')
            num_retry = os.environ.get('EVALUATION_NUM_RETRY', '3')
            model_args.extend([
                f'model={model_name}',
                f'base_url={meta.server_url}',
                f'num_concurrent={num_concurrent}',
                f're_try={num_retry}',
            ])
            if tasks in localtasks:
                tokenizer = os.environ.get('EVALUATION_MODEL_TOKENIZER') or ''
                if len(tokenizer) > 0:
                    model_args.extend([
                        f'tokenizer={tokenizer}',
                        'tokenized_requests=False',
                    ])
            cache_path = os.environ.get('EVALUATION_CACHE_PATH')
            if cache_path and not self.dry_run:
                cachepath = os.path.join(cache_path, tasks)
                self._args.extend([
                    '--use_cache', cachepath
                ])
        else:
            raise RuntimeError(f"unsupported model url: {meta.server_url}")

        if os.environ.get('EVALUATION_MODEL_ARGS'):
            model_args_map = dict(x.split('=') for x in model_args)
            model_args_map.update(dict(x.split('=') for x in os.environ['EVALUATION_MODEL_ARGS'].split(',')))
            model_args = [f'{key}={val}' for key, val in model_args_map.items()]
        if tasks in ['mbpp_plus']:
            self._args.append('--confirm_run_unsafe_code')
        self._args.extend([
            '--model_args', ','.join(model_args),
        ])

        if os.environ.get('EVALUATION_GEN_KWARGS'):
            gen_kwargs_map = (dict(x.split('=') for x in os.environ['EVALUATION_GEN_KWARGS'].split(',')))
            gen_kwargs = [f'{key}={val}' for key, val in gen_kwargs_map.items()]
            self._args.extend([
                '--gen_kwargs', ','.join(gen_kwargs),
            ])

        if len(self.gpu_ids) == 1:
            self._args.extend([
                '--device', f'cuda:{self.gpu_ids[0]}',
            ])

        if self.dry_run:
            self._args.extend([
                 '--limit', '5',
                 '--log_samples',
            ])
        self.num_fewshot = num_fewshot

    def create_datasets(self) -> List[Dataset]:
        return [DummyDataset(self.meta.name)]

    def execute(self, instance: RequestState) -> RequestState:
        instance.record_init_at()
        instance.record_request_at()
        cmd = [sys.executable, "-m", "lm_eval"] + self._args
        print(cmd)
        subprocess.check_call(cmd)
        instance.record_response_at()
        raw = []
        golds = []
        request = {}
        response = None
        for (dirname, _, files) in os.walk(self._output_path):
            for item in files:
                json_file = os.path.join(dirname, item)
                print(f"Finding JSON files in output directory, got {json_file}")
                if json_file.endswith(".json"):
                    with open(json_file) as f:
                        _, scope = os.path.split(json_file)
                        item = json.load(f)
                        item['__scope'] = scope
                        raw.append(item)
                if json_file.endswith('.jsonl'):
                    samples = []
                    print(f"Finding Sample files in output directory, got {json_file}")
                    with open(json_file) as f:
                        for line in f:
                            print(line)
                            val = json.loads(line)
                            samples.append(val)
                            if not golds and self.dry_run:
                                golds = [val['target']]
                                request = {
                                    'prompt': val['arguments']['gen_args_0']['arg_0'][0],
                                }
                                if 'resps' in val:
                                    response = {
                                        'completions': [
                                            {
                                                'text': t
                                            }
                                            for v in val['resps']
                                            for t in v
                                        ]
                                    }
                    raw.append({'__scope': 'samples', 'samples': samples})
        return replace(instance, raw={'states': raw}, golds=golds, request=request, response=response)

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
