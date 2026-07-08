import datasets
from datetime import datetime
from typing import List, Dict

from lm_eval.tasks.livebench.livebench_evaluator import gen_judgment

import pdb
def process_docs(dataset: datasets.Dataset) -> datasets.Dataset:
    def _process_doc(doc):
        if 'livebench_release_date' in doc.keys() and isinstance(doc['livebench_release_date'], datetime):
            doc['livebench_release_date_str'] = datetime.strftime(doc['livebench_release_date'], '%Y-%m-%d')
        if 'release_date' in doc.keys() and isinstance(doc['release_date'], datetime):
            doc['release_date'] = datetime.strftime(doc['release_date'], '%Y-%m-%d')

        if 'livebench_removal_date' in doc.keys() and isinstance(doc['livebench_removal_date'], datetime):
            doc['livebench_removal_date'] = datetime.strftime(doc['livebench_removal_date'], '%Y-%m-%d')

        if 'original_json' in doc.keys() and 'contest_date' in doc['original_json'].keys() and isinstance(doc['original_json']['contest_date'], datetime):
            doc['original_json']['contest_date'] = datetime.strftime(doc['original_json']['contest_date'], '%Y-%m-%d %H:%M:%S')
        return doc
    
    return dataset.map(_process_doc, remove_columns=["livebench_release_date"]).filter(lambda x: x["livebench_release_date_str"] in {'2024-08-31' '2024-07-26', '2024-06-24'})
    #return dataset.map(_process_doc, remove_columns=["livebench_release_date"]).filter(lambda x: x.get("livebench_removal_date") in {'2024-08-31', ''})
    # return dataset.map(_process_doc, remove_columns=["livebench_release_date"])
def doc_to_text(doc):
    return doc['turns'][0]

def process_results(doc: dict, results: List[str]) -> Dict[str, int]:

    model_answer = {"question_id": doc['question_id'], "choices": [{"index": 0, "turns": [results[0]]}]}
    
    subset_name = doc['category']
    task = doc['task']
    
    # if gen_judgment(doc, model_answer, subset_name, task, "test_id"):
    #     retval = 1
    # else:
    #     retval = 0

    results = {
        "exact_match": gen_judgment(doc, model_answer, subset_name, task, "test_id"),
    }
    return results

