import base64
import json
import logging
import os

from typing import Dict, Any, Optional, Tuple, List

import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from retry import retry

logger = logging.getLogger(__name__)


class ExecutorError(Exception):
    pass


class ExecutorService:
    def __init__(self, model_root: str, conf: Dict[str, Any], result: Dict[str, Any]):
        self.model_root: str = model_root
        self.conf = conf
        self.result = result
        self.result_prefix: str = result.get('prefix') or ''

    @classmethod
    def create_instance(cls):
        return cls(**settings.SSH_EXECUTOR)

    @property
    def job_root(self) -> str:
        return self.result['job_root']

    def build_environ_vars(
            self,
            download_job_id: str,
            batch_id: int,
            domain: str,
            environ: Optional[Dict[str, str]] = None,
            try_sequence: int = 0,
    ) -> Dict[str, str]:
        _environ: Dict[str, str] = {}
        if environ is not None:
            _environ.update(environ)
        model_path = os.path.join(self.model_root, download_job_id)
        log_path = self.get_log_path(batch_id, 'app', try_sequence)

        _environ['PIP_CACHE_DIR'] = os.path.join(self.model_root, "pip-cache")
        _environ['OUTPUT_DIR'] = self.job_root
        _environ['OUTPUT_PREFIX'] = self._get_prefix(try_sequence)
        val = (settings.STORAGE_DATASETS.get(domain) or {})
        for pkg, conf in val.items():
            pkg = pkg.upper()
            _environ[f'{pkg}_DATASET_DOWNLOAD_ID'] = conf['DOWNLOAD_ID']
            _environ[f'{pkg}_DATASET_DOWNLOAD_PATH'] = os.path.join(
                self.model_root,
                conf['DOWNLOAD_ID'],
            )
        _environ['MODEL_PATH'] = model_path
        _environ['THIRD_PARTY'] = os.path.join(model_path, "__paneval__")
        _environ['LOG_PATH'] = log_path
        _environ['EVAL_LOG_PATH'] = self.get_log_path(batch_id, 'eval', try_sequence)
        _environ['FEAM_VENV'] = os.path.join(_environ['THIRD_PARTY'], '/tmp/venv')
        _environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        _environ['HF_HOME'] = '/share/project/huggingface-240306' # Update this to refresh huggingface cache
        # # https://huggingface.co/docs/transformers/installation#offline-mode
        # _environ['HF_DATASETS_OFFLINE'] = '1'
        # _environ['TRANSFORMERS_OFFLINE'] = '1'
        return _environ

    def get_log_path(self, batch_id: int, kind: str, try_sequence: int) -> str:
        prefix = self._get_prefix(try_sequence)
        return os.path.join(
            self.job_root,
            f'{prefix}{batch_id}-{kind}.log',
        )

    def get_result_name(self, try_sequence: int, name: str) -> str:
        prefix = self._get_prefix(try_sequence)
        return f'{prefix}{name}'

    def load_batch_delayed_dags(self, batch_id: int, package: str, try_sequence: int):
        filename = f'batch-{batch_id}-package-{package}-delayed-dags.json'
        return self._load_serving_json(filename, try_sequence)

    def load_batch_status(self, batch_id: int, try_sequence: int):
        filename = f'batch-{batch_id}-status.json'
        return self._load_serving_json(filename, try_sequence)

    def load_batch_result(self, batch_id: int, try_sequence: int):
        batch_results: Dict[str, Any] = {}
        for seq in range(0, try_sequence + 1):
            filename = f'batch-{batch_id}-result.json'
            results = self._load_serving_json(filename, seq)
            if results is None:
                continue

            for key, val in results.items():
                current = batch_results.get(key) or {}
                details = current.get("details") or {}

                if isinstance(details, (list, tuple)):
                    details_by_key = {x['key']: x for x in details}
                    for d in val['details']:
                        details_by_key[d['key']] = d
                    current['details'] = list(details_by_key.values())

                current.update(val)
                batch_results[key] = current

        return batch_results or None

    def load_batch_dataset_result(self, batch_id: int, try_sequence: int, dataset_id: int, disturbance: str):
        filename = f'batch-{batch_id}-dataset-{dataset_id}-disturbance-{disturbance}.json'
        return self._load_serving_json(filename, try_sequence)

    def load_batch_dag_result(self, batch_id: int, try_sequence: int, dag_or_delayed_id: str):
        filename = f'batch-{batch_id}-dag-{dag_or_delayed_id}.json'
        return self._load_serving_json(filename, try_sequence)

    def download_mm_result_tar(self, batch_id: int, try_sequence: int) -> bytes:
        resp = self._load_serving_file(f'batch-{batch_id}.tar.gz', try_sequence)
        return resp.content

    def load_clcc_result(self, batch_id: int, try_sequence: int, dag_id: str):
        filename = f'batch-{batch_id}-dag-{dag_id}-clcc.json'
        return self._load_serving_json(filename, try_sequence)

    def _load_serving_json(self, filename: str, try_sequence: int) -> Optional[Any]:
        try:
            return self._do_load_serving_json(filename, try_sequence)
        except json.JSONDecodeError:
            logger.error(f"Load {filename} failed with error", exc_info=True)
            return None

    @retry(exceptions=(json.JSONDecodeError, requests.ConnectionError), tries=5, delay=2, backoff=2)
    def _do_load_serving_json(self, filename: str, try_sequence: int) -> Optional[Any]:
        response = self._load_serving_file(filename, try_sequence)
        if response.status_code == 404:
            return None
        json_content = response.text
        if filename.endswith('base64'):
            json_content = base64.b64decode(json_content)
        return json.loads(json_content)

    def _load_serving_file(
            self, filename: str,
            try_sequence: int,
            range_: Optional[Tuple[int, int]]=None,
    ):
        headers = {}
        if range_ is not None:
            start, end = range_
            headers['Range'] = f'bytes={start}-{end}'
        return requests.get(
            self._get_serving_url(filename, try_sequence),
            auth=self._get_serving_basic(),
            headers=headers,
        )

    def head_serving_file(self, filename: str, try_sequence: int) -> int:
        resp = requests.head(
            self._get_serving_url(filename, try_sequence),
            auth=self._get_serving_basic(),
        )
        if resp.status_code == 404:
            return 0
        return int(resp.headers['Content-Length'])

    def _get_serving_url(self, filename: str, try_sequence: int) -> str:
        if filename.startswith('env/'):
            prefix = ''
        else:
            prefix = self._get_prefix(try_sequence)
        return  f'{self.result["serving_host"]}{prefix}{filename}'


    def _get_serving_basic(self) -> HTTPBasicAuth:
        username = self.result['authentication']['username']
        password = self.result['authentication']['password']
        return HTTPBasicAuth(username, password)

    def count_log_page(self, batch_id: int, kind: str, try_sequence: int, page_size: int = 8096) -> int:
        filename = self._get_log_filename(batch_id, kind)
        content_length = self.head_serving_file(filename, try_sequence)
        return int(content_length / page_size) + 1

    def load_log(
            self, batch_id: int, kind: str, try_sequence: int,
            page: int = 1, page_size: int = 8096,
    ) -> str:

        start = (page - 1) * page_size
        end = start + page_size - 1
        filename = self._get_log_filename(batch_id, kind)
        response = self._load_serving_file(filename, try_sequence, range_=(start, end))
        if response.status_code == 404:
            return ""
        return response.text

    def _get_log_filename(self, batch_id: int, kind: str) -> str:
        if kind.startswith('env/log.'):
            return kind
        if kind in ["app", "eval"]:
            kind = f'{kind}.log'

        return f'{batch_id}-{kind}'

    def online_ssh_exe_cmd(self, ssh_cmd: str) -> List[str]:
        try:
            host = self.conf['online_ssh_host']
        except TypeError:
            host = self.conf['online_ssh_host']
        port = str(self.conf.get('online_ssh_port') or 22)
        cmd = [
            'ssh', "-o", "StrictHostKeyChecking no",
            '-CAXY', host,
            "-p", port,
            ssh_cmd,
        ]
        logger.info("gen online ssh cmd %s", ' '.join(cmd))
        return cmd

    def online_scp_to_remote(self, local: str, dst: str) -> List[str]:
        try:
            host = self.conf['online_ssh_host']
        except TypeError:
            host = self.conf['online_ssh_host']
        port = str(self.conf.get('online_ssh_port') or 22)
        cmd = [
            'scp', "-o", "StrictHostKeyChecking no",
            "-P", port,
            '-r', local,
            host + f':{dst}',
        ]
        logger.info("gen online scp cmd %s", ' '.join(cmd))
        return cmd

    def online_rsync_to_remote(self, local: str, dst: str) -> List[str]:
        try:
            host = self.conf['online_ssh_host']
        except TypeError:
            host = self.conf['online_ssh_host']
        port = str(self.conf.get('online_ssh_port') or 22)
        cmd = [
            'rsync', '-av', '-e', f'ssh -p {port}',
            local,
            host + f':{dst}',
        ]
        logger.info("gen online rsync cmd %s", ' '.join(cmd))
        return cmd

    def _get_prefix(self, try_sequence: int) -> str:
        if try_sequence == 0:
            return self.result_prefix
        return self.result_prefix + f'try-{try_sequence}-'

service = ExecutorService.create_instance()
