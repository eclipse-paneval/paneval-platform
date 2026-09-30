register_dataset = {"vqa_cp_dataset.py": "VqaCpDataset"}

dataset = dict(
    type="VqaCpDataset",
    ques_file="vqa_data_ann/VQA-CP/vqacp_v2_test_questions.json",
    anno_file="vqa_data_ann/VQA-CP/vqacp_v2_test_annotations.json",
    data_root="/share/project/datasets_cv/coco",
    sample_rate=0.1,
    prompt_template=dict(type="PromptTemplate"),
    name="vqacp",
)

evaluator = dict(type="CocoEvaluator")
