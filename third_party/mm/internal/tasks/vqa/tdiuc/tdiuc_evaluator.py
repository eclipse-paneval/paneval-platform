import csv
import json
from num2words import num2words
import numpy as np
from collections import defaultdict
from scipy import stats

import os.path as osp
from evalmm.registry import EVALUATORS
from evalmm.evaluator import BaseEvaluator


def mpt(predictions, gt_ann, answerkey):
    """
    MPT is the standard evaluation metric for TDIUC. Here we make reference to:
    (https://kushalkafle.com/projects/tdiuc.html)
    """
    res = defaultdict(list)
    gt_answers_idx = []
    notfound = 0
    question_types = set()
    predictions_index = []
    for raw_pred in predictions:
        question_id = raw_pred["question_id"]
        gt_answer = gt_ann[str(question_id)]["answer"][0]
        gt_type = gt_ann[str(question_id)]["question_type"]
        pred = int(answerkey.get(raw_pred["answer"], -1))
        predictions_index.append(pred)
        res[gt_type + "_pred"].append(pred)
        if answerkey.get(gt_answer) is not None:
            gt_idx = int(answerkey[gt_answer])
            res[gt_type + "_gt"].append(gt_idx)
            gt_answers_idx.append(gt_idx)
            if gt_idx == pred:
                res[gt_type + "_t"].append(pred)
            else:
                res[gt_type + "_f"].append(pred)
        else:
            gt_answers_idx.append(-1)
            res[gt_type + "_f"].append(pred)
            res[gt_type + "_gt"].append(-1)
            notfound += 1
        question_types.add(gt_type)
    print("\n%d of validation answers were not in the answerkey" % notfound)
    sum_acc = []
    eps = 1e-10
    print("\nNOT USING PER-ANSWER NORMALIZATION\n")
    result = {
        "Not_Per_Answer_Normalization": {},
        "Per_Answer_Normalization": {},
        "Overall_Traditional_Accuracy": {},
    }
    for tp in question_types:
        acc = 100 * (len(res[tp + "_t"]) / len(res[tp + "_t"] + res[tp + "_f"]))
        sum_acc.append(acc + eps)
        print("Accuracy for %s is %.2f" % (tp, acc))
        result["Not_Per_Answer_Normalization"][tp] = round(acc, 2)

    arithmetic_MPT = np.mean(np.array(sum_acc))
    harmonic_MPT = stats.hmean(sum_acc)
    print("Arithmetic MPT Accuracy is %.2f" % (arithmetic_MPT))
    print("Harmonic MPT Accuracy is %.2f" % (harmonic_MPT))
    result["Not_Per_Answer_Normalization"]["Arithmetic MPT"] = round(arithmetic_MPT, 2)
    result["Not_Per_Answer_Normalization"]["Harmonic MPT"] = round(harmonic_MPT, 2)
    print("\n---------------------------------------")
    print("USING PER-ANSWER NORMALIZATION\n")

    sum_acc = []
    eps = 1e-10
    for tp in question_types:
        per_ans_stat = defaultdict(int)
        for g, p in zip(res[tp + "_gt"], res[tp + "_pred"]):
            per_ans_stat[str(g) + "_gt"] += 1
            if g == p:
                per_ans_stat[str(g)] += 1
        unq_acc = 0
        for unq_ans in set(res[tp + "_gt"]):
            acc_curr_ans = (
                per_ans_stat[str(unq_ans)] / per_ans_stat[str(unq_ans) + "_gt"]
            )
            unq_acc += acc_curr_ans
        acc = 100 * unq_acc / len(set(res[tp + "_gt"]))
        sum_acc.append(acc + eps)
        print("Accuracy for %s is %.2f" % (tp, acc))
        result["Per_Answer_Normalization"][tp] = round(acc, 2)

    arithmetic_N_MPT = np.mean(np.array(sum_acc))
    harmonic_N_MPT = stats.hmean(sum_acc)
    print("Arithmetic N-MPT Accuracy is %.2f" % (arithmetic_N_MPT))
    print("Harmonic N-MPT Accuracy is %.2f" % (harmonic_N_MPT))
    result["Per_Answer_Normalization"]["Arithmetic N-MPT"] = round(arithmetic_N_MPT, 2)
    result["Per_Answer_Normalization"]["Harmonic N-MPT"] = round(harmonic_N_MPT, 2)

    n_acc = 100 * np.mean(predictions_index == np.array(gt_answers_idx))
    print("Overall Traditional Accuracy is %.2f" % n_acc)
    result["agg_metrics"] = result["Overall_Traditional_Accuracy"] = round(n_acc, 2)

    return result


def tdiuc_preprocess(results):
    # from "1" to "one"
    for pred in results:
        answer = pred["answer"]
        answer = answer.lower()
        # if answer.startswith("no "):
        #     answer = "doesnotapply"
        answer = answer.split(", ")
        count_num = [an.isdigit() for an in answer]
        if sum(count_num) == len(answer):
            if len(answer) >= 2:
                print(answer)
            answer = [num2words(ans) for ans in answer]
        pred["answer"] = ", ".join(answer)
        pred["question_id"] = int(pred["question_id"])
    return results


@EVALUATORS.register_module()
class TdiucEvaluator(BaseEvaluator):
    def __init__(self, csv_file, **kwargs) -> None:
        self.csv_file = csv_file

    def process(self, dataset, output_dir, **kwargs):
        """
        Args:
            dataset (Dataset): dataset instance
            answers (list): list of answers
        """
        # annotation = dataset.get_annotation()
        dataset_name = dataset.name
        result_file = osp.join(output_dir, dataset_name + ".json")

        answerkey_csv = csv.reader(open(self.csv_file))
        answerkey = dict((rows[0], rows[1]) for rows in answerkey_csv)

        gt_ann = dataset.get_annotation()
        answers = json.load(open(result_file))
        answers = tdiuc_preprocess(answers)
        # predictions = np.array(predictions)
        results = mpt(answers, gt_ann, answerkey)
        results["accuracy"] = results.pop("agg_metrics")
        self.save(results, answers, dataset_name, output_dir)
        return results
