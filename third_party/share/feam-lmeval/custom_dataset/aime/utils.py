import re
from typing import Dict, List, Optional
import datasets


def evaluate(pred, gold):
    # pred 里有 {}来包含答案，需要先取出{}的内容再和gold做比较
    pred = re.findall(r'\{(.*?)\}', pred)
    if len(pred) == 0:
        return False
    pred = pred[-1]
    gold = gold.replace(" ", "")
    pred = pred.replace(" ", "")
    # print(pred, gold)
    if pred == gold:    
        return True
    else:
        return False

def process_results(doc: dict, results: List[str]) -> Dict[str, int]:
    prediction = results[0]
    groundtruth = doc['gold_answer']
    prediction = prediction.split("</think>")[-1]

    if evaluate(prediction, groundtruth):
        retval = 1
    else:
        retval = 0

    results = {
        "exact_match": retval,
    }
    return results


if __name__ == "__main__":
    import json
    with open('/Users/xuan/code/lm-evaluation-harness/lm_eval/tasks/quant_bench/quantQA_vali.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Save the modified data back to JSON
    with open('s8.json', 'w', encoding='utf-8') as file:
        for line in data:
            file.write(json.dumps(line, ensure_ascii=False)+"\n")

    from datasets import load_dataset

    ds = load_dataset("json", data_files="/Users/xuan/code/lm-evaluation-harness/lm_eval/tasks/quant_bench/quantQA_vali.json")