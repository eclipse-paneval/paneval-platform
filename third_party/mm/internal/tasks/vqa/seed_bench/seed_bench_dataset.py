import json
import os.path as osp
from evalmm.registry import DATASETS, PROMPTS
from evalmm.dataset.vqa_base_dataset import VqaBaseDataset


@DATASETS.register_module()
class SeedBenchDataset(VqaBaseDataset):
    def __init__(
        self,
        data_root,
        anno_file,
        name,
        prompt_template=None,
        data_types=("image",),
        debug=False,
        with_label=False,
        **kwargs,
    ):
        self.data_root = data_root
        self.annotations = self.load_annotation(data_root, anno_file)
        self.name = name
        if prompt_template is not None:
            prompt_template = PROMPTS.build(prompt_template)
        self.prompt_template = prompt_template
        self.with_label = with_label or debug
        self.data_types = set(data_types)
        if debug:
            self.annotations = self.annotations[:32]
        self.filter_data()

    def load_annotation(self, data_root, anno_file):
        annotations = json.load(open(osp.join(data_root, anno_file)))["questions"]
        for ann in annotations:
            ann["question_type"] = "multiple-choice"
        return annotations

    def filter_data(self):
        self.annotations = [
            row for row in self.annotations if row["data_type"] in self.data_types
        ]

    def build_prompt(self, annotation):
        question = "<image 1> " + annotation["question"]
        base = ord("A")
        choices = ["a", "b", "c", "d"]
        for i, choice in enumerate(choices):
            question += "\n" + chr(base + i) + ". " + annotation[f"choice_{choice}"]
        if self.prompt_template is not None:
            question = self.prompt_template.build_prompt(
                annotation={"question": question, "question_type": "multiple-choice"}
            )
        return question

    def __getitem__(self, index):
        annotation = self.annotations[index]
        question = self.build_prompt(annotation)
        ret = {
            "img_path": [
                osp.join(
                    self.data_root,
                    "SEED-Bench-image-jpg",
                    annotation["data_id"] + ".jpg",
                )
            ],
            "question": question,
            "question_id": str(annotation["question_id"]),
            "type": "multiple-choice",
        }
        if self.with_label:
            ret["label"] = annotation["answer"]
        return ret
