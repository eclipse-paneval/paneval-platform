import json
import os.path as osp
import pandas as pd
from torch.utils.data import Dataset
from evalmm.registry import DATASETS, PROMPTS


@DATASETS.register_module()
class ScienceQaDataset(Dataset):
    def __init__(
        self,
        data_root,
        ques_file,
        name,
        prompt_template=None,
        with_hint=False,
        debug=False,
        with_label=True,
        **kwargs,
    ):
        sqa_data = json.load(open(osp.join(data_root, ques_file)))
        sqa_pd = pd.DataFrame(sqa_data).T
        self.questions = sqa_pd[
            (sqa_pd["split"] == "test") & (sqa_pd["image"] == "image.png")
        ]
        self.name = name
        if prompt_template is not None:
            prompt_template = PROMPTS.build(prompt_template)
        self.prompt_template = prompt_template
        self.debug = debug
        self.with_hint = with_hint
        if self.debug:
            self.questions = self.questions[:32]
        self.qids = self.questions.index
        self.img_root = osp.join(data_root, "test")
        self.with_label = with_label or debug

    def __len__(self):
        return len(self.questions)

    def build_prompt(self, index):
        data = self.questions.iloc[index]
        question = data["question"]
        context = data["hint"]
        choices = data["choices"]
        base = ord("A")
        if self.with_hint and context:
            question = f"Context: {context}\n{question}"
        for i, choice in enumerate(choices):
            question += "\n" + chr(base + i) + ". " + choice
        question = "<image 1> " + question
        if self.prompt_template is not None:
            question = self.prompt_template.build_prompt(
                annotation={"question": question, "question_type": "multiple-choice"}
            )

        return question

    def __getitem__(self, index):
        question_id = self.qids[index]
        question = self.build_prompt(index)
        img_path = osp.join(self.img_root, question_id, "image.png")
        ret = {
            "img_path": [img_path],
            "question": question,
            "question_id": question_id,
            "type": "multiple-choice",
        }
        if self.with_label:
            ret["label"] = chr(self.questions.iloc[index]["answer"] + ord("A"))
        return ret

    def meta_info(self):
        return {"name": self.name, "length": len(self.questions), "type": "vqa"}

    def get_annotation(self):
        anno_dict = {}  # question_id: answer
        for i in range(len(self.questions)):
            row = self.questions.iloc[i]
            anno_dict[self.qids[i]] = {
                "answer": chr(row["answer"] + ord("A")),
                "grade": row["grade"],
                "topic": row["topic"],
                "category": row["category"],
                "question_type": "multiple-choice",
            }
        return anno_dict
