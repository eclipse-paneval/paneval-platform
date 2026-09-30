register_dataset = {"../vqa2.0/vqa_coco_dataset.py": "VqaCocoDataset"}
register_evaluator = {"tdiuc_evaluator.py": "TdiucEvaluator"}

dataset = dict(
    type="VqaCocoDataset",
    ques_file="vqa_data_ann/TDIUC/OpenEnded_mscoco_val2014_questions.json",
    anno_file="vqa_data_ann/TDIUC/mscoco_val2014_annotations.json",
    data_root="/share/project/datasets_cv/coco",
    prompt_template=dict(type="PromptTemplate"),
    sample_rate=0.1,
    name="tdiuc",
)

evaluator = dict(
    type="TdiucEvaluator",
    csv_file="/share/project/datasets_cv/coco/vqa_data_ann/TDIUC/sample_answerkey.csv",
)
