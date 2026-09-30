import os.path as osp
import json
from torch.utils.data import Dataset
from evalmm.registry import DATASETS, PROMPTS


@DATASETS.register_module()
class VqaCocoDataset(Dataset):
    def __init__(
        self,
        data_root,
        ques_file,
        name,
        prompt_template=None,
        anno_file=None,
        debug=False,
        sample_rate=1.0,
        with_label=False,
         **kwargs,
    ):
        """
        img_root (string): Root directory of images (e.g. coco/images/)
        ques_path (string): Question file
        """
        self.img_root = osp.join(data_root, "images/val2014")
        self.name = name
        if prompt_template is not None:
            prompt_template = PROMPTS.build(prompt_template)
        self.prompt_template = prompt_template
        self.anno_file = osp.join(data_root, anno_file)
        self.questions = json.load(open(osp.join(data_root, ques_file)))["questions"]
        self.debug = debug
        self.with_label = with_label or debug
        if self.with_label:
            self.annotation = self.get_annotation()
        if sample_rate < 1.0:
            sampled_num = int(len(self.questions) * sample_rate)
            gap = len(self.questions) // sampled_num
            self.questions = self.questions[::gap]
        if debug:
            self.questions = self.questions[:32]

    def __getitem__(self, index):
        per_question = self.questions[index]
        question = "<image 1>" + per_question["question"]
        if self.prompt_template is not None:
            question = self.prompt_template.build_prompt(
                annotation={"question": question, "question_type": "short-answer"}
            )

        question_id = per_question["question_id"]
        image_id = str(per_question["image_id"])
        length = len(image_id)
        image_id = str(0) * (12 - length) + image_id + ".jpg"
        image_id = "COCO_val2014_" + image_id
        img_path = osp.join(self.img_root, image_id)
        ret = {
            "img_path": [img_path],
            "question": question,
            "question_id": str(question_id),
            "type": "short-answer",
        }
        if self.with_label:
            ret["label"] = self.annotation[str(question_id)]["answer"][0]
        return ret

    def __len__(self):
        return len(self.questions)

    def meta_info(self):
        return {"name": self.name, "length": len(self.questions), "type": "vqa"}

    def get_annotation(self):
        gt_annotations = json.load(open(self.anno_file))["annotations"]
        gt_dict = {}
        for gt in gt_annotations:
            gt_refactor = {"question_id": str(gt["question_id"])}
            answers = []
            for ans in gt["answers"]:
                answers.append(ans["answer"])
            gt_refactor["answer"] = answers
            gt_refactor["question_type"] = gt.get("question_type", None)
            gt_dict[str(gt["question_id"])] = gt_refactor
        return gt_dict
