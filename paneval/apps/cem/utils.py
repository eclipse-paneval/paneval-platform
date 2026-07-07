"""Utilities."""
import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Any

from django.conf import settings

from paneval import storage
from ..evaluation.models import Evaluation, DatasetDisturbance, MmDataset
from ..evaluation.models import CvTaskResult
from ..evaluation.models import PretrainedTokenizer, PretrainedTokenizerFile
from . import models


logger = logging.getLogger(__name__)


@dataclass
class Options:
    model: str
    "The model name to evaluate."

    server_url: str
    "The request url of the evaluated service."

    extras: Dict[str, Any] = field(default_factory=dict)
    "Extra options for scenario-specific usage."


def get_nlp_scenario_options(
        eva: Evaluation, *,
        max_eval_instances=1000,
        dry_run: bool=False,
) -> Options:
    model_name = eva.name
    tokenizer = eva.tokenizer
    return  Options(
        server_url=eva.url,
        model=model_name,
        extras={
            'max_eval_instances': max_eval_instances,
            'dry_run': dry_run,
            'tokenizer': tokenizer,
        },
    )


def download_tokenizer(pk: int) -> str:
    tk = PretrainedTokenizer.objects.get(pk=pk)
    dest = os.path.join(settings.TOKENIZER_BASE_PATH, str(pk))
    if not os.path.exists(dest):
        os.makedirs(dest)

    for item in PretrainedTokenizerFile.objects.filter(
            tokenizer_id=pk,
            deleted_at=None,
    ):
        fdest = os.path.join(dest, item.filename)
        if os.path.exists(fdest):
            continue
        key = os.path.join(tk.ks3_key, item.filename)
        fobj = storage.store.get_key(key)
        if fobj is None:
            raise RuntimeError(f"download file {key} from ks3 failed")
        with open(fdest, 'wb') as f:
            f.write(fobj.read())
    return dest


def copy_tokenizer_to(pk: int, new_ks3_key: str):
    tk = PretrainedTokenizer.objects.get(pk=pk)
    for item in PretrainedTokenizerFile.objects.filter(
            tokenizer_id=pk,
            deleted_at=None,
    ):
        new_key = os.path.join(new_ks3_key, item.filename)
        key = os.path.join(tk.ks3_key, item.filename)
        fobj = ks3.get_key(key)
        if fobj is None:
            raise RuntimeError("unexcepted behavior")
        logger.info(f'copying tokenizer file from {key} to {new_key}')
        ks3.upload(new_key, fobj.read())

def summarize_mm_batch(batch: models.Batch, eva: Evaluation) -> List[Dict[str, Any]]:
    res = []
    a = CvTaskResult.objects.filter(batch_id=batch.pk)
    for item in a:
        data = item.result_json
        if "data" in data and data["data"]["ret"] == 1 and data.get("lbx", 0) == 0:
            temp = data["data"]["data"]
            cur = {}
            if data["name"] == "vqa" or data["name"] == "图问答":
                if data["dataset"] == "chart_qa":
                    cur["accuracy"] = temp["relaxed_accuracy"]
                elif data["dataset"] == "cmmu":
                    cur["accuracy"] = temp["test-overall"]["accuracy"]
                else:
                    cur["accuracy"] = temp["accuracy"]
            elif data["name"] == "t2i" or data["name"] == "文本生成图像":
                cur["accuracy"] = temp.get("FID", 0)
                if "IS" in temp:
                    del temp["IS"]
            elif data["name"] == "retrieval" or data["name"] == "图像-文本匹配":
                cur["accuracy"] = temp["i2t_R@1"]
            elif data["name"] == "t2v" or data["name"] == "文生视频":
                cur["accuracy"] = temp["总体印象"]

            dict1 = {
                    "science_qa": "ScienceQA(test)",
                    "mmmu": "MMMU(val)",
                    "seed_bench": "SEED-Bench(test)",
                    "cmmu": "CMMU(test)",
                    "cmmmu": "CMMMU(val)",
                    "math_vista": "MathVista(testmini)",
                    "mm_bench_cn": "MMBench-CN(val)",
                    "mm_bench_en": "MMBench(val)",
                    "hallusion_bench": "HallusionBench(img)",
                    "coco_t2i": "COCO_val2014",
                    "cub": "CUB-200-2011",
                    "flowers": "Flowers102",
                    "mg18_zh": "MG-18_zh",
                    "mg18_en": "MG-18_en",
                    "Subjective_all": "Subjective_all",
                    "Subjective_zh": "Subjective_zh",
                    "Subjective_en": "Subjective_en",
                }
            if data["dataset"] in dict1:
                cur["key"] = dict1[data["dataset"]]
            else:
                cur["key"] = data["dataset"]

            cur["dataset_id"] = item.mid
            cur["task_name"] = data["name"]
            cur["data"] = data
            res.append(cur)
    return [{"disturbance": "", "details": res}]


def summarize_robustness(batch: models.Batch) -> List[Dict[str, Any]]:
    disturbance_groups: Dict[str, str] = {
        x.name: x.group
        for x in DatasetDisturbance.objects.all()
    }
    orig_results: List[Dict[str, Any]] = []
    dist_results_by_group: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in batch.results:
        if 'disturbance' not in item:
            continue
        if item['disturbance'] == '':
            orig_results.append(item)
        else:
            group = disturbance_groups[item['disturbance']]
            dist_results_by_group[group].append(item)
    for group, dist_results in dist_results_by_group.items():
        if len(orig_results) > 0 and len(dist_results) > 0:
            _calc_robustness(group, orig_results, dist_results)
    return batch.results


def _calc_robustness(group: str, originals: List[Dict[str, Any]], disturbances: List[Dict[str, Any]]):
    acc_dists_by_dataset_key = defaultdict(list)
    for result in disturbances:
        for d in result['details']:
            acc_dists_by_dataset_key[d['key']].append(d['accuracy'] or 0)

    for original in originals:
        d: Dict[str, Any]
        for d in original['details']:
            if d['key'] not in acc_dists_by_dataset_key:
                continue

            acc_orig = d['accuracy'] or 0.0000000001
            acc_dists = acc_dists_by_dataset_key[d['key']]
            t = len(acc_dists)
            diff_sum = sum([acc_orig - (acc_dist or 0) for acc_dist in acc_dists])
            robustness = (1/(t * acc_orig)) * diff_sum
            d.setdefault('robustnesses', {})
            d['robustnesses'][group] = robustness


def change_permissions_recursive(path):
    mode = 0o777
    os.chmod(path, mode)
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            os.chmod(dir_path, mode)
            change_permissions_recursive(dir_path)
        for file in files:
            file_path = os.path.join(root, file)
            os.chmod(file_path, mode)


def merge_lbx(eva: Evaluation):
    return merge_lbx_config(eva.datasets_config, eva.include_robustness)


def merge_lbx_batch(batch: models.Batch):
    return merge_lbx_config(batch.datasets_config, batch.include_robustness)


def merge_lbx_config(datasets_config: List[Dict[str, Any]], include_robustness=True):
    data = []
    for item in datasets_config:
        md = MmDataset.objects.get(id=item["id"])
        md.data["pk"] = md.pk
        md.data["cv_id"] = md.cv_id
        md.data["lbx"] = md.lbx
        data.append(md.data)
        if include_robustness:
            mds = MmDataset.objects.filter(cv_id=md.cv_id, lbx=1)
            for item1 in mds:
                if item1.data["is_admin"] > -1 and item1.data.get("parent", -1) == md.pk:
                    item1.data["pk"] = item1.pk
                    item1.data["cv_id"] = item1.cv_id
                    item1.data["lbx"] = item1.lbx
                    data.append(item1.data)
    return data
