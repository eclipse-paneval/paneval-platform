from collections import defaultdict
from evalmm.evaluator import BaseEvaluator
from evalmm.registry import EVALUATORS


@EVALUATORS.register_module()
class MmbenchEvaluator(BaseEvaluator):
    def cal_accuracy(self, annotation, answers):
        right = 0
        shift = int(1e6)
        result_collect = defaultdict(list)
        for answer in answers:
            question_id = str(answer["question_id"])
            gt = annotation[question_id]
            if gt["question_type"] == "multiple-choice":
                is_correct = self.evaluate_multiple_choice(gt, answer)
            else:
                raise NotImplementedError
            answer["correct"] = is_correct
            result_collect[int(question_id) % shift].append(is_correct)
            answer["label"] = gt["answer"]

        for k, v in result_collect.items():
            if all(v):
                right += 1
        return {"accuracy": right / len(result_collect) * 100}
