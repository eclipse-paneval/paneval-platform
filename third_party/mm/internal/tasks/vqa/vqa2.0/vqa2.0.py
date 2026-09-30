register_dataset = {"vqa_coco_dataset.py": "VqaCocoDataset"}

dataset = dict(
    type="VqaCocoDataset",
    ques_file="vqa_data_ann/VQA2.0/v2_OpenEnded_mscoco_val2014_questions.json",
    data_root="/share/project/datasets_cv/coco",
    anno_file="vqa_data_ann/VQA2.0/v2_mscoco_val2014_annotations.json",
    sample_rate=0.1,
    prompt_template=dict(type="PromptTemplate"),
    name="vqa2.0",
)

evaluator = dict(type="CocoEvaluator")
