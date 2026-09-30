register_evaluator = {"ocrlite_evaluator.py": "OcrLiteEvaluator"}

dataset = dict(
    type="VqaBaseDataset",
    data_root="/share/project/mmdataset/ocrlite/ocrlite_zh",
    anno_file="data.json",
    prompt_template=dict(type="PromptTemplate", post_prompt=""),
    name="ocrlite_zh",
)

evaluator = dict(
    type="OcrLiteEvaluator",
)
