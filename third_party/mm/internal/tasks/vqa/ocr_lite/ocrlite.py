register_evaluator = {"ocrlite_evaluator.py": "OcrLiteEvaluator"}

dataset = dict(
    type="VqaBaseDataset",
    data_root="/share/project/hezheqi/projects/OCRLiteData/ocrlite_v1",
    anno_file="data.json",
    prompt_template=dict(type="PromptTemplate", post_prompt=""),
    name="ocrlite",
)

evaluator = dict(
    type="OcrLiteEvaluator",
)
